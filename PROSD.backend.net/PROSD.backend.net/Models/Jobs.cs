namespace PROSD.backend.net.Models
{
    public class Job
    {
        public int Id { get; set; }

        public string Title { get; set; } = "";

        public string Description { get; set; } = "";

        public string Status { get; set; } = "Queued";

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}