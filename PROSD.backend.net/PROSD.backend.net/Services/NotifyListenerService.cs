using Microsoft.AspNetCore.SignalR;
using Npgsql;
using PROSD.backend.net.Hubs;
using PROSD.backend.net.Data;

namespace PROSD.backend.net.Services;

// Цей сервіс прослуховує події PostgreSQL NOTIFY на каналі "job_completed"
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

    // Цей метод працює у фоновому режимі та прослуховує події PostgreSQL NOTIFY
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await using var conn = new NpgsqlConnection(_connString);
        await conn.OpenAsync(ct);

        conn.Notification += async (_, e) => await HandleNotify(e.Payload, ct);

        await using var cmd = new NpgsqlCommand("LISTEN job_completed;", conn);
        await cmd.ExecuteNonQueryAsync(ct);

        _logger.LogInformation("Listening for PostgreSQL NOTIFY on channel: job_completed");

        while (!ct.IsCancellationRequested)
        {
            await conn.WaitAsync(ct);
        }
    }

    // Цей метод викликається коли отримується подія NOTIFY він отримує ідентифікатор завдання з корисного навантаження
    // отримує деталі завдання з бази даних зчитує вивід зі сховища та надсилає сповіщення клієнту через SignalR
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

            var output = await storage.ReadOutputAsync(job.S3FolderPath!);

            if (!string.IsNullOrEmpty(job.ConnectionId))
            {
                await _hub.Clients.Client(job.ConnectionId)
                    .SendAsync("JobCompleted", new
                    {
                        jobId = job.Id,
                        status = job.Status,
                        output = output
                    }, ct);

                _logger.LogInformation("Sent JobCompleted for JobId {JobId} to client {ConnectionId}", job.Id, job.ConnectionId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing NOTIFY for JobId {JobId}", jobId);
        }
    }
}