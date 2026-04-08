using Microsoft.AspNetCore.Mvc;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Services;

namespace PROSD.backend.net.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class JobsController : ControllerBase
    {
        private readonly JobService _jobService;

        public JobsController(JobService jobService)
        {
            _jobService = jobService;
        }

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

            return Accepted(new
            {
                jobId = job.Id,
                status = job.Status,
                s3FolderPath = job.S3FolderPath
            });
        }

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
    }
}