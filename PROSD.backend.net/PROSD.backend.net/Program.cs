using Microsoft.EntityFrameworkCore;
using Minio;
using PROSD.backend.net.Data;
using PROSD.backend.net.Middleware;
using PROSD.backend.net.Services;

var builder = WebApplication.CreateBuilder(args);

// Controllers + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// PostgreSQL
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// Cache
builder.Services.AddMemoryCache();

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

var app = builder.Build();

// Middleware
app.UseMiddleware<ExceptionHandlingMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.MapControllers();

app.Run();