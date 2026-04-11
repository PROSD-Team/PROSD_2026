using Microsoft.AspNetCore.SignalR;
using Npgsql;
using PROSD.backend.net.Hubs;
using PROSD.backend.net.Data;
using PROSD.backend.net.Models;

namespace PROSD.backend.net.Services;

/// <summary>
/// Фоновий сервіс, який прослуховує події PostgreSQL (NOTIFY) 
/// та сповіщає клієнтів через SignalR про завершення конвеєра.
/// </summary>
public class NotifyListenerService : BackgroundService
{
    private readonly IHubContext<PipelineHub> _hub;
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly string _connString;
    private readonly ILogger<NotifyListenerService> _logger;

    public NotifyListenerService(
        IHubContext<PipelineHub> hub,
        IServiceScopeFactory scopeFactory,
        IConfiguration config,
        ILogger<NotifyListenerService> logger)
    {
        _hub = hub;
        _scopeFactory = scopeFactory;
        _connString = config.GetConnectionString("DefaultConnection")!;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await using var conn = new NpgsqlConnection(_connString);
        await conn.OpenAsync(ct);

        conn.Notification += async (_, e) => await HandleNotify(e.Payload, ct);

        // Підписуємося на канал "job_completed", який викликається тригером у PostgreSQL
        await using var cmd = new NpgsqlCommand("LISTEN job_completed;", conn);
        await cmd.ExecuteNonQueryAsync(ct);

        _logger.LogInformation("Listening for PostgreSQL NOTIFY on channel: job_completed");

        // Тримаємо підключення відкритим
        while (!ct.IsCancellationRequested)
        {
            await conn.WaitAsync(ct);
        }
    }

    private async Task HandleNotify(string jobIdStr, CancellationToken ct)
    {
        if (string.IsNullOrEmpty(jobIdStr) || !int.TryParse(jobIdStr, out var jobId))
        {
            _logger.LogWarning("Received invalid NOTIFY payload: {Payload}", jobIdStr);
            return;
        }

        try
        {
            using var scope = _scopeFactory.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var storage = scope.ServiceProvider.GetRequiredService<StorageService>();

            var job = await db.Jobs.FindAsync(new object[] { jobId }, ct);
            if (job == null)
            {
                _logger.LogWarning("Job with ID {JobId} not found in database.", jobId);
                return;
            }

            // --- АРХІТЕКТУРА ROUTING SLIP ---
            // Gateway більше не керує кроками. Ми реагуємо ТІЛЬКИ на фінальні статуси.
            // Проміжні статуси (наприклад, перехід між мікросервісами) ігноруються.
            if (job.Status == "completed" || job.Status == "failed")
            {
                _logger.LogInformation("Job {JobId} finished with status '{Status}'. Notifying client.", job.Id, job.Status);
                await SendToClientAsync(job, storage, ct);
            }
            else
            {
                // Опційне логування для відстеження конвеєра в консолі бекенду
                _logger.LogInformation("Job {JobId} is at intermediate status '{Status}' (Step {CurrentStep}). Waiting for pipeline to finish.", job.Id, job.Status, job.CurrentStepIndex);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing NOTIFY for JobId {JobId}", jobId);
        }
    }

    private async Task SendToClientAsync(Job job, StorageService storage, CancellationToken ct)
    {
        // Якщо клієнт не підключений через WebSocket (наприклад, зробив запит через Swagger), просто виходимо
        if (string.IsNullOrEmpty(job.ConnectionId))
        {
            return;
        }

        string output = string.Empty;
        try
        {
            // Зчитуємо фінальний результат з MinIO (output.json)
            output = await storage.ReadOutputAsync(job.S3FolderPath!);
        }
        catch (Exception)
        {
            _logger.LogWarning("Output file not found in MinIO for JobId {JobId}. Proceeding with fallback message.", job.Id);
            output = "Файл результатів (output.json) не знайдено у сховищі.";
        }

        // Відправляємо дані конкретному клієнту
        await _hub.Clients.Client(job.ConnectionId)
            .SendAsync("JobCompleted", new
            {
                jobId = job.Id,
                status = job.Status,
                output = output
            }, ct);

        _logger.LogInformation("Sent SignalR update for JobId {JobId} to client {ConnectionId}", job.Id, job.ConnectionId);
    }
}