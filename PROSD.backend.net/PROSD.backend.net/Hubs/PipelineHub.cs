using Microsoft.AspNetCore.SignalR;

namespace PROSD.backend.net.Hubs
{
    public class PipelineHub : Hub
    {
        private readonly ILogger<PipelineHub> _logger;

        public PipelineHub(ILogger<PipelineHub> logger)
        {
            _logger = logger;
        }

        public override async Task OnConnectedAsync()
        {
            Console.WriteLine($"Client connected: {Context.ConnectionId}");
            _logger.LogInformation("Client connected: {ConnectionId}", Context.ConnectionId);
            await base.OnConnectedAsync();
        }

        public override async Task OnDisconnectedAsync(Exception? ex)
        {
            Console.WriteLine($"Client disconnected: {Context.ConnectionId}");
            _logger.LogInformation("Client disconnected: {ConnectionId}", Context.ConnectionId);
            await base.OnDisconnectedAsync(ex);
        }
    }
}
