using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace PROSD.backend.net.Models;

public class Pipeline
{
    [Key]
    public int Id { get; set; }

    [Required]
    public Guid UserId { get; set; }

    public UserAccount User { get; set; } = null!;

    [Required]
    public string Name { get; set; } = null!;

    [Required]
    [Column(TypeName = "jsonb")]
    public string DefinitionJson { get; set; } = null!;

    public int? ParentPipelineId { get; set; }

    public Pipeline? ParentPipeline { get; set; }

    public ICollection<Pipeline> Branches { get; set; } = new List<Pipeline>();

    public ICollection<Job> Jobs { get; set; } = new List<Job>();

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
