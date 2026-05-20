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
        public DbSet<UserAccount> Users { get; set; }
        public DbSet<Pipeline> Pipelines { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<Pipeline>()
                .HasOne(p => p.User)
                .WithMany(u => u.Pipelines)
                .HasForeignKey(p => p.UserId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Pipeline>()
                .HasOne(p => p.ParentPipeline)
                .WithMany(p => p.Branches)
                .HasForeignKey(p => p.ParentPipelineId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Job>()
                .HasOne(j => j.User)
                .WithMany(u => u.Jobs)
                .HasForeignKey(j => j.UserId)
                .OnDelete(DeleteBehavior.SetNull);

            modelBuilder.Entity<Job>()
                .HasOne(j => j.Pipeline)
                .WithMany(p => p.Jobs)
                .HasForeignKey(j => j.PipelineId)
                .OnDelete(DeleteBehavior.SetNull);
        }
    }
}
