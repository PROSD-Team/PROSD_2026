using Microsoft.Extensions.Caching.Memory;
using PROSD.backend.net.Data;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Models;

namespace PROSD.backend.net.Services
{
    public class JobService
    {
        private readonly AppDbContext _context;
        private readonly ILogger<JobService> _logger;
        private readonly IMemoryCache _cache;
        private readonly StorageService _storageService;

        public JobService(
            AppDbContext context,
            ILogger<JobService> logger,
            IMemoryCache cache,
            StorageService storageService)
        {
            _context = context;
            _logger = logger;
            _cache = cache;
            _storageService = storageService;
        }

        public async Task<Job> CreateJobAsync(CreateJobRequest request)
        {
            var folderPath = _storageService.GenerateFolderPath();
            var configYaml = _storageService.BuildConfigYaml(
                request.PipelineSteps,
                request.ParametersJson,
                request.ConnectionId
            );

            await _storageService.SaveConfigAsync(folderPath, configYaml);

            await using var transaction = await _context.Database.BeginTransactionAsync();

            try
            {
                var job = new Job
                {
                    Status = "pending",
                    PipelineSteps = request.PipelineSteps,
                    CurrentStepIndex = 0,
                    TargetWorker = string.IsNullOrWhiteSpace(request.TargetWorker)
                        ? GetFirstWorker(request.PipelineSteps)
                        : request.TargetWorker,
                    S3FolderPath = folderPath,
                    ConnectionId = request.ConnectionId,
                    CreatedAt = DateTime.UtcNow,
                    StartedAt = null,
                    RetryCount = 0
                };

                _context.Jobs.Add(job);
                await _context.SaveChangesAsync();
                await transaction.CommitAsync();

                _logger.LogInformation(
                    "Job created with Id {JobId}, FolderPath {FolderPath}",
                    job.Id,
                    folderPath
                );

                return job;
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, "Error while creating job");
                throw;
            }
        }

        public async Task<Job?> GetJobById(int id)
        {
            string cacheKey = $"job_{id}";
            if (_cache.TryGetValue(cacheKey, out Job? cachedJob))
            {
                _logger.LogInformation("Job {JobId} returned from cache", id);
                return cachedJob;
            }

            // ТУТ ЗМІНА: FindAsync замість Find під час декількох запитів. якщо буде синхроні запити до бд то
            // ми втрачаємо сенс оборобляти запити від веб серверу асинхроно бо потоки будуть вставати в чергу
            // на доступ до бд і чекати поки інший потік звільнить доступ до бд. FindAsync дозволяє не блокувати
            // потоки а відпускати їх для обробки інших запитів, поки вони чекають на результат від бд 
            var job = await _context.Jobs.FindAsync(id);

            if (job != null)
            {
                _cache.Set(cacheKey, job, TimeSpan.FromMinutes(5));
                _logger.LogInformation("Job {JobId} saved to cache", id);
            }
            else
            {
                _logger.LogWarning("Job with Id {JobId} not found", id);
            }

            return job;
        }

        private string GetFirstWorker(string pipelineSteps)
        {
            if (string.IsNullOrWhiteSpace(pipelineSteps))
                return "unknown";

            var firstStep = pipelineSteps
                .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .FirstOrDefault();

            return string.IsNullOrWhiteSpace(firstStep) ? "unknown" : firstStep;
        }
    }
}