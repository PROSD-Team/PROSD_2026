using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace PROSD.backend.net.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddJobNotifyTrigger : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                CREATE OR REPLACE FUNCTION notify_job_change()
                RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify('job_completed', NEW.""Id""::text);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER job_status_trigger
                AFTER UPDATE OF ""Status"" ON ""Jobs""
                FOR EACH ROW
                WHEN (NEW.""Status"" = 'completed' OR NEW.""Status"" = 'failed')
                EXECUTE FUNCTION notify_job_change();");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("DROP TRIGGER IF EXISTS job_status_trigger ON \"Jobs\";");
            migrationBuilder.Sql("DROP FUNCTION IF EXISTS notify_job_change();");
        }
    }
}
