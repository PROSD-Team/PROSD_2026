using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using PROSD.backend.net.Data;
using PROSD.backend.net.Models;

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

    /// <summary>
    /// Самореєстрація алгоритму/мікросервісу при його запуску НЕ ТРОГАТЬ БЛЯТЬ ФРОНТЕНДЕРАМ ЦЕ ЗВ'ЗОК МІЖ МІКРОСЕРВІСОМ І БЕКОМ 
    /// Запит: POST /api/meta/register
    /// </summary>
    /// <param name="metadata">Метадані алгоритму для реєстрації</param>
    /// <returns>Результат реєстрації алгоритму</returns>
    [HttpPost("register")]
    public async Task<IActionResult> RegisterAlgorithm([FromBody] AlgorithmMetadata metadata)
    {
        _logger.LogInformation("[AlgorithmService] Received registration request for '{Algorithm}' in '{Category}'", metadata.Name, metadata.Category);

        // Шукаємо, чи алгоритм вже зареєстрований
        var existingAlgo = await _dbContext.Algorithm
            .FirstOrDefaultAsync(a => a.Category == metadata.Category && a.Name == metadata.Name);

        if (existingAlgo != null)
        {
            // Оновлюємо існуючий (на випадок якщо схема чи опис змінилися)
            existingAlgo.Description = metadata.Description;
            existingAlgo.InputSchema = metadata.InputSchema;
            existingAlgo.IsActive = metadata.IsActive;

            _dbContext.Algorithm.Update(existingAlgo);
            _logger.LogInformation("Updated metadata for '{Algorithm}'", metadata.Name);
        }
        else
        {
            // Реєструємо новий
            // Якщо Id приходить порожнім з воркера, генеруємо новий
            if (string.IsNullOrEmpty(metadata.Id))
            {
                metadata.Id = Guid.NewGuid().ToString();
            }

            await _dbContext.Algorithm.AddAsync(metadata);
            _logger.LogInformation("Registered new algorithm '{Algorithm}'", metadata.Name);
        }

        await _dbContext.SaveChangesAsync();

        return Ok(new { message = "Алгоритм успішно зареєстровано", id = metadata.Id ?? existingAlgo?.Id });
    }
}