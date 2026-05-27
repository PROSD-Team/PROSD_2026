using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using PROSD.backend.net.Data;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Services;

namespace PROSD.backend.net.Controllers
{
    /// <summary>
    /// Контролер для управління асинхронними завданнями (Job Pipelines).
    /// Відповідає за прийом конвеєрів на обробку та перевірку їх поточного статусу.
    /// </summary>
    [ApiController]
    [Route("api/[controller]")]
    public class JobsController : ControllerBase
    {
        private readonly JobService _jobService;
        private readonly AppDbContext _dbContext;

        public JobsController(JobService jobService, AppDbContext dbContext)
        {
            _jobService = jobService;
            _dbContext = dbContext;
        }

        /// <summary>
        /// Створює нове завдання (конвеєр) для асинхронної обробки.
        /// </summary>
        /// <remarks>
        /// Цей метод приймає дані конвеєра, створює запис у базі даних та повертає статус 202 Accepted.
        /// У заголовку Location відповіді буде знаходитись URL для подальшої перевірки статусу цього завдання.
        /// </remarks>
        /// <param name="request">Об'єкт з даними для створення завдання (кроки, connectionId, параметри тощо).</param>
        /// <returns>Повертає ідентифікатор створеного завдання та його початковий статус.</returns>
        /// <response code="202">Завдання успішно прийнято в обробку (очікує виконання).</response>
        /// <response code="400">Передано некоректні дані (наприклад, відсутні обов'язкові поля).</response>
        /// <response code="500">Внутрішня помилка сервера при збереженні завдання.</response>
        [HttpPost]
        [ProducesResponseType(StatusCodes.Status202Accepted)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        [ProducesResponseType(StatusCodes.Status500InternalServerError)]
        public async Task<IActionResult> CreateJob([FromBody] CreateJobRequest request)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var job = await _jobService.CreateJobAsync(request);

            // Використовуємо AcceptedAtAction для правильного генерування Location Header
            return AcceptedAtAction(
                actionName: nameof(GetJobStatus),
                routeValues: new { id = job.Id },
                value: new
                {
                    jobId = job.Id,
                    status = job.Status,
                    s3FolderPath = job.S3FolderPath
                }
            );
        }

        /// <summary>
        /// Отримує поточний статус завдання за його ідентифікатором.
        /// </summary>
        /// <remarks>
        /// Цей ендпоінт призначений для поллінгу (polling), якщо клієнт не використовує SignalR.
        /// Він повертає поточний крок, на якому знаходиться конвеєр, та цільовий воркер.
        /// </remarks>
        /// <param name="id">Унікальний ідентифікатор завдання (Job ID).</param>
        /// <returns>Детальна інформація про поточний стан виконання завдання.</returns>
        /// <response code="200">Статус завдання успішно отримано.</response>
        /// <response code="404">Завдання з вказаним ідентифікатором не існує в базі даних.</response>
        /// <response code="500">Внутрішня помилка сервера.</response>
        [HttpGet("{id}/status")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        [ProducesResponseType(StatusCodes.Status500InternalServerError)]
        public async Task<IActionResult> GetJobStatus(int id)
        {
            var job = await _jobService.GetJobById(id);

            if (job == null)
            {
                return NotFound(new
                {
                    message = $"Job with id {id} not found"
                });
            }

            return Ok(new
            {
                jobId = job.Id,
                status = job.Status,
                currentStep = job.CurrentStepIndex,
                targetWorker = job.TargetWorker
            });
        }

        /// <summary>
        /// Отримує історію запусків алгоритмів для конкретного користувача.
        /// </summary>
        /// <param name="userId">Ідентифікатор користувача.</param>
        /// <returns>Список виконаних Job-ів.</returns>
        [HttpGet("history")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public async Task<IActionResult> GetHistory([FromQuery] Guid userId)
        {
            if (userId == Guid.Empty)
            {
                return BadRequest(new { message = "userId is required." });
            }

            var history = await _dbContext.Jobs
                .AsNoTracking()
                .Include(j => j.Pipeline)
                .Where(j => j.UserId == userId)
                .OrderByDescending(j => j.CreatedAt)
                .Select(j => new
                {
                    jobId = j.Id,
                    status = j.Status,
                    pipelineSteps = j.PipelineSteps,
                    pipelineId = j.PipelineId,
                    pipelineName = j.Pipeline != null ? j.Pipeline.Name : null,
                    createdAt = j.CreatedAt
                })
                .ToListAsync();

            return Ok(history);
        }
    }
}
