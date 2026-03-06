using Prometheus;
using Serilog;
using Serilog.Formatting.Json;
using Serilog.Sinks.Grafana.Loki;
using Microsoft.OpenApi.Models;
using System.Text;
using System.Text.Json;

// TODO: REMOVE THIS. This is just an example of event emitting, should not get into any form of final version

Serilog.Debugging.SelfLog.Enable(Console.Error);

var builder = WebApplication.CreateBuilder(args);

// --- Feature flags ---
var enableMetrics = Environment.GetEnvironmentVariable("ENABLE_METRICS") != "false";
var enableLogging = Environment.GetEnvironmentVariable("ENABLE_LOGGING") != "false";

// Serilog configuration
var loggerConfig = new LoggerConfiguration()
    .WriteTo.Console(new JsonFormatter())  // JSON output works best for Loki
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "PROSD-Gateway")
    .Enrich.WithProperty("Environment", Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Development");

if (enableLogging)
{
    var lokiUrl = Environment.GetEnvironmentVariable("LOKI_URL") ?? "http://loki:3100";
    var labels = new[] { new LokiLabel { Key = "app", Value = "gateway" } };
    loggerConfig.WriteTo.GrafanaLoki(lokiUrl, labels: labels);
    Log.Information("✅ Loki logging enabled at {LokiUrl} with labels", lokiUrl);
}

Log.Logger = loggerConfig.CreateLogger();
builder.Host.UseSerilog();

// --- Services ---
builder.Services.AddControllers();

// Swagger/OpenAPI
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "PROSD API",
        Version = "v1"
    });
});

// Prometheus metrics
if (enableMetrics)
{
    builder.Services.AddMetrics();
}

var app = builder.Build();

// --- Middleware & pipeline ---
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "PROSD API v1");
    });
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

// Metrics endpoint
if (enableMetrics)
{
    app.UseHttpMetrics();
    app.MapMetrics();
    Log.Information("✅ Prometheus metrics enabled at /metrics");
}

// Health check
app.MapGet("/health", () => Results.Ok(new
{
    status = "healthy",
    timestamp = DateTime.UtcNow,
    service = "PROSD-Gateway"
}));


app.MapGet("/test-loki", async () =>
{
    using var client = new HttpClient();

    // Calculate nanoseconds manually (works on .NET 6+)
    var now = DateTimeOffset.UtcNow;
    var nanos = now.ToUnixTimeMilliseconds() * 1_000_000;

    var payload = new
    {
        streams = new[]
        {
            new
            {
                stream = new { app = "gateway-test" },
                values = new[]
                {
                    new[]
                    {
                        nanos.ToString(),
                        "test log from gateway"
                    }
                }
            }
        }
    };

    // Serialize to JSON
    var json = JsonSerializer.Serialize(payload);

    // Prepare HTTP content
    using var content = new StringContent(json, Encoding.UTF8, "application/json");

    // Send to Loki
    var response = await client.PostAsync("http://loki:3100/loki/api/v1/push", content);

    return response.IsSuccessStatusCode ? Results.Ok("ok") : Results.Problem($"failed: {response.StatusCode}");
});

// --- Run ---
try
{
    Log.Information("🚀 Starting PROSD Gateway Service");
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
