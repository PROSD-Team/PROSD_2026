using Microsoft.AspNetCore.Connections;
using Microsoft.AspNetCore.Mvc;
using PROSD.backend.net.Data;
using PROSD.backend.net.Models;
using RabbitMQ.Client;
using System.Text;
using System.Text.Json;

namespace PROSD.backend.net.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class JobsController : ControllerBase
    {
        private readonly AppDbContext _context;

        public JobsController(AppDbContext context)
        {
            _context = context;
        }

        [HttpPost]
        public async Task<IActionResult> CreateJob([FromBody] Job request)
        {
            if (request == null)
                return BadRequest("Request body is required.");

            if (string.IsNullOrWhiteSpace(request.Title))
                return BadRequest("Title is required.");

            var job = new Job
            {
                Title = request.Title,
                Description = request.Description,
                Status = "Queued",
                CreatedAt = DateTime.UtcNow
            };

            _context.Jobs.Add(job);
            _context.SaveChanges();

            var factory = new ConnectionFactory
            {
                HostName = "localhost"
            };

            await using var connection = await factory.CreateConnectionAsync();
            await using var channel = await connection.CreateChannelAsync();

            await channel.QueueDeclareAsync(
                queue: "jobs",
                durable: false,
                exclusive: false,
                autoDelete: false,
                arguments: null);

            var message = JsonSerializer.Serialize(job);
            var body = Encoding.UTF8.GetBytes(message);

            await channel.BasicPublishAsync(
                exchange: string.Empty,
                routingKey: "jobs",
                body: body);

            return Ok(new
            {
                message = "Job created successfully",
                jobId = job.Id,
                status = job.Status,
                createdAt = job.CreatedAt
            });
        }

        [HttpGet("{id}")]
        public IActionResult GetJob(int id)
        {
            var job = _context.Jobs.FirstOrDefault(j => j.Id == id);

            if (job == null)
                return NotFound("Job not found");

            return Ok(job);
        }
    }
}