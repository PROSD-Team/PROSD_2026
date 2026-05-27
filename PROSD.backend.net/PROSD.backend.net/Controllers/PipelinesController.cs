using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using PROSD.backend.net.Data;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Models;

namespace PROSD.backend.net.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PipelinesController : ControllerBase
{
    private readonly AppDbContext _dbContext;
    private readonly ILogger<PipelinesController> _logger;

    public PipelinesController(AppDbContext dbContext, ILogger<PipelinesController> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> GetPipelines([FromQuery] Guid userId)
    {
        if (userId == Guid.Empty)
        {
            return BadRequest(new { message = "userId is required." });
        }

        var pipelines = await _dbContext.Pipelines
            .Where(p => p.UserId == userId)
            .OrderByDescending(p => p.UpdatedAt)
            .Select(p => new
            {
                id = p.Id,
                name = p.Name,
                definitionJson = p.DefinitionJson,
                parentPipelineId = p.ParentPipelineId,
                createdAt = p.CreatedAt,
                updatedAt = p.UpdatedAt
            })
            .ToListAsync();

        return Ok(pipelines);
    }

    [HttpGet("{id:int}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetPipeline(int id, [FromQuery] Guid userId)
    {
        var pipeline = await _dbContext.Pipelines
            .Where(p => p.Id == id && p.UserId == userId)
            .Select(p => new
            {
                id = p.Id,
                name = p.Name,
                definitionJson = p.DefinitionJson,
                parentPipelineId = p.ParentPipelineId,
                createdAt = p.CreatedAt,
                updatedAt = p.UpdatedAt
            })
            .FirstOrDefaultAsync();

        if (pipeline == null)
        {
            return NotFound(new { message = "Pipeline not found." });
        }

        return Ok(pipeline);
    }

    [HttpPost]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> CreatePipeline([FromBody] PipelineRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var userExists = await _dbContext.Users.AnyAsync(u => u.Id == request.UserId);
        if (!userExists)
        {
            return BadRequest(new { message = "User not found." });
        }

        var pipeline = new Pipeline
        {
            UserId = request.UserId,
            Name = request.Name.Trim(),
            DefinitionJson = request.DefinitionJson,
            ParentPipelineId = request.ParentPipelineId,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _dbContext.Pipelines.Add(pipeline);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Pipeline created: {PipelineId}", pipeline.Id);

        return CreatedAtAction(nameof(GetPipeline), new { id = pipeline.Id, userId = request.UserId }, new
        {
            id = pipeline.Id,
            name = pipeline.Name,
            definitionJson = pipeline.DefinitionJson,
            parentPipelineId = pipeline.ParentPipelineId,
            createdAt = pipeline.CreatedAt,
            updatedAt = pipeline.UpdatedAt
        });
    }

    [HttpPut("{id:int}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdatePipeline(int id, [FromBody] PipelineUpdateRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var pipeline = await _dbContext.Pipelines.FirstOrDefaultAsync(p => p.Id == id && p.UserId == request.UserId);
        if (pipeline == null)
        {
            return NotFound(new { message = "Pipeline not found." });
        }

        pipeline.Name = request.Name.Trim();
        pipeline.DefinitionJson = request.DefinitionJson;
        pipeline.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync();

        return Ok(new
        {
            id = pipeline.Id,
            name = pipeline.Name,
            definitionJson = pipeline.DefinitionJson,
            parentPipelineId = pipeline.ParentPipelineId,
            createdAt = pipeline.CreatedAt,
            updatedAt = pipeline.UpdatedAt
        });
    }

    [HttpPost("{id:int}/branch")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> BranchPipeline(int id, [FromBody] BranchPipelineRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var source = await _dbContext.Pipelines.FirstOrDefaultAsync(p => p.Id == id && p.UserId == request.UserId);
        if (source == null)
        {
            return NotFound(new { message = "Pipeline not found." });
        }

        var pipeline = new Pipeline
        {
            UserId = request.UserId,
            Name = request.Name.Trim(),
            DefinitionJson = source.DefinitionJson,
            ParentPipelineId = source.Id,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _dbContext.Pipelines.Add(pipeline);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Pipeline branched: {PipelineId} from {ParentId}", pipeline.Id, source.Id);

        return CreatedAtAction(nameof(GetPipeline), new { id = pipeline.Id, userId = request.UserId }, new
        {
            id = pipeline.Id,
            name = pipeline.Name,
            definitionJson = pipeline.DefinitionJson,
            parentPipelineId = pipeline.ParentPipelineId,
            createdAt = pipeline.CreatedAt,
            updatedAt = pipeline.UpdatedAt
        });
    }
}
