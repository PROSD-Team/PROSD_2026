using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace PROSD.backend.net.Models;

public class AlgorithmMetadata
{
    [Key]
    public string Id { get; set; } = null!;

    [Required]
    public string Name { get; set; } = null!;

    [Required]
    public string Category { get; set; } = null!;

    public string? Description { get; set; }

    [Column(TypeName = "jsonb")]
    [Required]
    public string InputSchema { get; set; } = null!;

    public bool IsActive { get; set; } = true;
}