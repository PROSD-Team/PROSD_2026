using Microsoft.EntityFrameworkCore;
using PROSD.backend.net.Models;

namespace PROSD.backend.net.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<Job> Jobs { get; set; }
        public DbSet<AlgorithmMetadata> Algorithm { get; set; }
    }
}