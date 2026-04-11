namespace PROSD.backend.net.Models
{
    public class Job
    {
        public int Id { get; set; }

        public string Status { get; set; } = "pending";

        public string PipelineSteps { get; set; } = string.Empty;

        public int CurrentStepIndex { get; set; } = 0;

        public string? TargetWorker { get; set; }

        public string? S3FolderPath { get; set; }

        public string? ConnectionId { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime? StartedAt { get; set; }

        public int RetryCount { get; set; } = 0;
    }
}