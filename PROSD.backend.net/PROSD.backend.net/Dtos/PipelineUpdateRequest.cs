using System.ComponentModel.DataAnnotations;

namespace PROSD.backend.net.Dtos;

public class PipelineUpdateRequest
{
    [Required]
    public Guid UserId { get; set; }

    [Required]
    [MinLength(2)]
    public string Name { get; set; } = string.Empty;

    [Required]
    public string DefinitionJson { get; set; } = string.Empty;
}
