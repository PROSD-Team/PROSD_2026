using Microsoft.AspNetCore.Mvc;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Services;
using System.Threading.Tasks;

namespace PROSD.backend.net.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PipelineController : ControllerBase
{
    private readonly JobService _jobService;

    public PipelineController(JobService jobService)
        => _jobService = jobService;

    /// <summary>
    /// Приймає конвеєр від фронтенду, створює Job і повертає 202 Accepted
    /// </summary>
    [HttpPost]
    public async Task<IActionResult> Submit([FromBody] CreateJobRequest request)
    {
        var job = await _jobService.CreateJobAsync(request);

        return AcceptedAtAction(
            actionName: nameof(GetJobStatus),
            routeValues: new { id = job.Id },
            value: new { jobId = job.Id, status = job.Status }
        );
    }

    /// <summary>
    /// Ендпоінт для перевірки статусу (на нього вказує Location Header з 202 Accepted)
    /// </summary>
    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetJobStatus(int id)
    {
        var job = await _jobService.GetJobById(id); 

        if (job == null)
        {
            return NotFound(new { message = $"Завдання з ID {id} не знайдено." });
        }

        return Ok(new
        {
            jobId = job.Id,
            status = job.Status,
            currentStepIndex = job.CurrentStepIndex,
            targetWorker = job.TargetWorker,
            retryCount = job.RetryCount,
            createdAt = job.CreatedAt,
            startedAt = job.StartedAt
        });
    }
}