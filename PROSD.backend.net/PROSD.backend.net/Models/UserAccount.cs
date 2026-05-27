using System.ComponentModel.DataAnnotations;
using Microsoft.EntityFrameworkCore;

namespace PROSD.backend.net.Models;

[Index(nameof(Email), IsUnique = true)]
public class UserAccount
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    [EmailAddress]
    public string Email { get; set; } = null!;

    [Required]
    public string PasswordHash { get; set; } = null!;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<Pipeline> Pipelines { get; set; } = new List<Pipeline>();

    public ICollection<Job> Jobs { get; set; } = new List<Job>();
}
