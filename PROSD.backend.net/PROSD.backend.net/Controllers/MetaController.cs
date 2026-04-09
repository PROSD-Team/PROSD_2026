using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using PROSD.backend.net.Data;

namespace PROSD.backend.net.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MetaController : ControllerBase
{
    private readonly ILogger<MetaController> _logger;
    private readonly AppDbContext _dbContext;

    public MetaController(ILogger<MetaController> logger, AppDbContext dbContext)
    {
        _logger = logger;
        _dbContext = dbContext;
    }

    /// <summary>
    /// Отримання списку всіх доступних категорій та алгоритмів
    /// Запит: GET /api/meta/algorithms
    /// </summary>
    /// <param name="category">Опційний параметр для фільтрації за категорією</param>
    /// <returns>Список категорій та алгоритмів</returns>
    [HttpGet("algorithms")]
    public async Task<IActionResult> GetAlgorithmsList(string? category)
    {
        _logger.LogInformation("[AlgorithmService] Fetching categories and algorithms");

        var categories = await _dbContext.Algorithm
            .Where(a => a.IsActive)
            .GroupBy(a => a.Category)
            .Select(g => new
            {
                category = g.Key,
                algorithms = g.Select(a => new { id = a.Id, name = a.Name, description = a.Description })
            })
            .ToListAsync();

        _logger.LogInformation("[AlgorithmService] Retrieved {Count} categories", categories.Count);

        return Ok(categories);
    }

    /// <summary>
    /// Отримання JSON-схеми для вхідних даних конкретного алгоритму (для побудови UI)
    /// Запит: GET /api/meta/input/{category}/{algorithm}
    /// </summary>
    /// <param name="category">Категорія алгоритму</param>
    /// <param name="algorithm">Назва алгоритму</param>
    /// <returns>JSON-схема для вхідних даних алгоритму</returns>
    [HttpGet("input/{category}/{algorithm}")]
    public async Task<IActionResult> GetAlgorithmSchema(string category, string algorithm)
    {
        _logger.LogInformation("[AlgorithmService] Fetching JSON schema: Category='{Category}', Algorithm='{Algorithm}'", category, algorithm);

        var algo = await _dbContext.Algorithm
            .FirstOrDefaultAsync(a => a.Category == category && a.Name == algorithm && a.IsActive);

        if (algo == null)
        {
            _logger.LogWarning("[AlgorithmService] Algorithm '{Algorithm}' in category '{Category}' is missing or inactive.", algorithm, category);

            return NotFound(new { message = "Алгоритм не знайдено" });
        }

        _logger.LogInformation("[AlgorithmService] JSON schema for '{Algorithm}' successfully found and sent.", algorithm);

        return Content(algo.InputSchema, "application/json");
    }
}