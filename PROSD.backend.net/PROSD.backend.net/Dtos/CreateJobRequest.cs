using System.ComponentModel.DataAnnotations;

namespace PROSD.backend.net.Dtos
{
    public class CreateJobRequest
    {
        [Required]
        public string PipelineSteps { get; set; } = string.Empty;

        [Required]
        public string ConnectionId { get; set; } = string.Empty;

        [Required]
        public string ParametersJson { get; set; } = string.Empty;

        public string? TargetWorker { get; set; }
    }
}