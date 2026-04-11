using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace PROSD.backend.net.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HealthController : ControllerBase
    {
        private readonly ILogger<HealthController> _logger;

        public HealthController(ILogger<HealthController> logger)
        {
            _logger = logger;
        }

        [HttpGet]
        public IActionResult Get()
        {
            _logger.LogInformation("[HealthService] Health check requested.");
            return Ok(new { status = "Healthy" });
        }
    }
}