using Microsoft.EntityFrameworkCore;
using Minio;
using Prometheus;
using Serilog;
using Serilog.Formatting.Json;
using Serilog.Sinks.Grafana.Loki;
using PROSD.backend.net.Data;
using PROSD.backend.net.Hubs;
using PROSD.backend.net.Middleware;
using PROSD.backend.net.Services;
using System.Reflection;
using System.Text;

// --- Capture Serilog self-log errors ---
var selfLogWriter = new StringWriter();
Serilog.Debugging.SelfLog.Enable(selfLogWriter);
// Also echo to console error for immediate visibility
Serilog.Debugging.SelfLog.Enable(Console.Error);

// --- Feature flags (can be toggled via environment variables) ---
var enableMetrics = Environment.GetEnvironmentVariable("ENABLE_METRICS") != "false";
var enableLogging  = Environment.GetEnvironmentVariable("ENABLE_LOGGING") != "false";

Console.WriteLine($">>> enableLogging = {enableLogging}");
Console.WriteLine($">>> enableMetrics = {enableMetrics}");

// --- Configure Serilog ---
var loggerConfig = new LoggerConfiguration()
    .WriteTo.Console(new JsonFormatter())
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "PROSD-Backend")
    .Enrich.WithProperty("Environment", Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Development")
    .Enrich.WithMachineName()
    .Enrich.WithProcessId()
    .Enrich.WithThreadId();

if (enableLogging)
{
    var lokiUrl = Environment.GetEnvironmentVariable("LOKI_URL") ?? "http://loki:3100";
    Console.WriteLine($">>> Configuring Loki sink with URL: {lokiUrl}");
    try
    {
        loggerConfig.WriteTo.GrafanaLoki(
            lokiUrl,
            labels: new[] { new LokiLabel { Key = "app", Value = "backend" } }
        );
        Console.WriteLine(">>> Loki sink configuration completed.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($">>> ERROR configuring Loki sink: {ex}");
    }
}
else
{
    Console.WriteLine(">>> Loki logging is DISABLED by ENABLE_LOGGING.");
}

Log.Logger = loggerConfig.CreateLogger();

// --- Print any Serilog self-log errors ---
var selfLogErrors = selfLogWriter.ToString();
if (!string.IsNullOrEmpty(selfLogErrors))
{
    Console.WriteLine($">>> SERILOG SELF-LOG ERRORS:\n{selfLogErrors}");
}

try
{
    Log.Information("🚀 Starting PROSD Backend Service");

    if (enableLogging)
    {
        Log.Information("✅ Loki logging enabled at {LokiUrl}", Environment.GetEnvironmentVariable("LOKI_URL") ?? "http://loki:3100");
        Log.Error("🚨 Test error log – should appear in Loki");
    }

    var builder = WebApplication.CreateBuilder(args);

    // --- Replace default logging with Serilog ---
    builder.Host.UseSerilog();

    // --- Existing services (unchanged) ---
    builder.Services.AddControllers();
    builder.Services.AddEndpointsApiExplorer();
    builder.Services.AddSwaggerGen(options =>
    {
        var xmlFilename = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
        options.IncludeXmlComments(Path.Combine(AppContext.BaseDirectory, xmlFilename));
    });

    // PostgreSQL
    builder.Services.AddDbContext<AppDbContext>(options =>
        options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

    // Cache
    builder.Services.AddMemoryCache();
    builder.Services.AddSignalR();
    builder.Services.AddCors(options =>
    {
        options.AddPolicy("AlwaysSayYes", policy =>
        {
            policy.SetIsOriginAllowed(_ => true)
                  .AllowAnyMethod()
                  .AllowAnyHeader()
                  .AllowCredentials();
        });
    });

    // MinIO client
    builder.Services.AddSingleton<IMinioClient>(sp =>
    {
        var configuration = sp.GetRequiredService<IConfiguration>();
        var endpoint = configuration["Minio:Endpoint"];
        var accessKey = configuration["Minio:AccessKey"];
        var secretKey = configuration["Minio:SecretKey"];
        var useSsl = configuration.GetValue<bool>("Minio:UseSSL");

        var client = new MinioClient()
            .WithEndpoint(endpoint)
            .WithCredentials(accessKey, secretKey);

        if (useSsl) client = client.WithSSL();
        return client.Build();
    });

    // Services
    builder.Services.AddScoped<JobService>();
    builder.Services.AddScoped<StorageService>();
    builder.Services.AddHostedService<NotifyListenerService>();

    // --- Prometheus metrics (only if enabled) ---
    if (enableMetrics)
    {
        builder.Services.AddMetrics();
    }

    var app = builder.Build();

    // --- Database migration ---
    using (var scope = app.Services.CreateScope())
    {
        var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        dbContext.Database.Migrate();
    }

    // --- Middleware pipeline ---
    app.UseMiddleware<ExceptionHandlingMiddleware>();
    app.UseCors("AlwaysSayYes");

    if (app.Environment.IsDevelopment())
    {
        app.UseSwagger();
        app.UseSwaggerUI(options =>
        {
            options.SwaggerEndpoint("/swagger/v1/swagger.json", "v1");
            options.RoutePrefix = string.Empty;
        });
    }

    app.UseHttpsRedirection();
    app.UseAuthorization();

    // --- Prometheus metrics middleware (if enabled) ---
    if (enableMetrics)
    {
        app.UseHttpMetrics();
        app.MapMetrics();
        Log.Information("✅ Prometheus metrics enabled at /metrics");
    }

    app.MapControllers();
    app.MapHub<PipelineHub>("/hubs/pipeline");
    app.MapGet("/health", () => Results.Ok(new { status = "Healthy", timestamp = DateTime.UtcNow }));

    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "❌ Application terminated unexpectedly");
    throw;
}
finally
{
    Log.CloseAndFlush();
}