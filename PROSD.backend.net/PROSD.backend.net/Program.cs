using Microsoft.EntityFrameworkCore;
using Minio;
using PROSD.backend.net.Data;
using PROSD.backend.net.Hubs;
using PROSD.backend.net.Middleware;
using PROSD.backend.net.Services;
using System.Reflection;

var builder = WebApplication.CreateBuilder(args);

// Controllers + Swagger
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

builder.Services.AddCors(Options =>
{
    Options.AddPolicy("AlwaysSayYes", policy =>
    {
        policy.SetIsOriginAllowed(_ => true)
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
}
);

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

    if (useSsl)
    {
        client = client.WithSSL();
    }

    return client.Build();
});

// Services
builder.Services.AddScoped<JobService>();
builder.Services.AddScoped<StorageService>();
builder.Services.AddHostedService<NotifyListenerService>();

var app = builder.Build();

// Middleware
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

app.MapControllers();

app.MapHub<PipelineHub>("/hubs/pipeline");

app.Run();
