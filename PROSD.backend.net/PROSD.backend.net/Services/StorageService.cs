using System.Text;
using Minio;
using Minio.DataModel.Args;

namespace PROSD.backend.net.Services
{
    public class StorageService
    {
        private readonly IMinioClient _minioClient;
        private readonly IConfiguration _configuration;
        private readonly ILogger<StorageService> _logger;
        private readonly string _bucketName;

        public StorageService(
            IMinioClient minioClient,
            IConfiguration configuration,
            ILogger<StorageService> logger)
        {
            _minioClient = minioClient;
            _configuration = configuration;
            _logger = logger;
            _bucketName = _configuration["Minio:BucketName"] ?? "pipeline-runs";
        }

        public string GenerateFolderPath()
        {
            return $"pipeline_run_{DateTime.UtcNow:yyyyMMdd_HHmmss}_{Guid.NewGuid():N}";
        }

        public string BuildConfigYaml(string pipelineSteps, string parametersJson, string connectionId)
        {
            var sb = new StringBuilder();

            sb.AppendLine($"pipeline_steps: \"{pipelineSteps}\"");
            sb.AppendLine($"connection_id: \"{connectionId}\"");
            sb.AppendLine("parameters_json: |");

            foreach (var line in parametersJson.Split('\n'))
            {
                sb.AppendLine($"  {line.TrimEnd('\r')}");
            }

            return sb.ToString();
        }

        public async Task EnsureBucketExistsAsync()
        {
            var bucketExistsArgs = new BucketExistsArgs()
                .WithBucket(_bucketName);

            bool exists = await _minioClient.BucketExistsAsync(bucketExistsArgs);

            if (!exists)
            {
                var makeBucketArgs = new MakeBucketArgs()
                    .WithBucket(_bucketName);

                await _minioClient.MakeBucketAsync(makeBucketArgs);
                _logger.LogInformation("Bucket {BucketName} created", _bucketName);
            }
        }

        public async Task SaveConfigAsync(string folderPath, string configContent)
        {
            await EnsureBucketExistsAsync();

            var objectName = $"{folderPath}/config.yaml";
            var bytes = Encoding.UTF8.GetBytes(configContent);

            using var stream = new MemoryStream(bytes);

            var putObjectArgs = new PutObjectArgs()
                .WithBucket(_bucketName)
                .WithObject(objectName)
                .WithStreamData(stream)
                .WithObjectSize(stream.Length)
                .WithContentType("application/x-yaml");

            await _minioClient.PutObjectAsync(putObjectArgs);

            _logger.LogInformation("Config saved to MinIO: {ObjectName}", objectName);
        }

        public async Task<string> ReadOutputAsync(string folderPath)
        {
            var objectName = $"{folderPath}/output.json";
            var result = new StringBuilder();

            try
            {
                var getObjectArgs = new GetObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithCallbackStream(stream =>
                    {
                        using var reader = new StreamReader(stream);
                        result.Append(reader.ReadToEnd());
                    });

                await _minioClient.GetObjectAsync(getObjectArgs);
                return result.ToString();
            }
            catch (Exception ex) 
            { 
                _logger.LogError(ex, "Error reading output from MinIO: {ObjectName}", objectName);
                throw new InvalidOperationException($"Failed to read output from storage for object '{objectName}'.", ex);
            }
        }
    }
}