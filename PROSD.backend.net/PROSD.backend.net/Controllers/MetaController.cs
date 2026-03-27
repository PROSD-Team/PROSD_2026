using Microsoft.AspNetCore.Mvc;

namespace PROSD.backend.net.Controllers;

[ApiController]
[Route("api/[controller]")]
public class MetaController : ControllerBase
{
    /// <summary>
    /// Отримання списку всіх доступних категорій та алгоритмів
    /// Запит: GET /api/meta/algorithms
    /// </summary>
    [HttpGet("algorithms")]
    public IActionResult GetAlgorithmsList()
    {
        // Заглушка (mock) замість запиту до БД
        var mockAlgorithms = new[]
        {
            new
            {
                Category = "text-processing",
                Algorithms = new[]
                {
                    new { Name = "random-texts", Description = "Генерація випадкового тексту" },
                    new { Name = "text-cleaner", Description = "Очищення тексту від спецсимволів" }
                }
            },
            new
            {
                Category = "static-properties",
                Algorithms = new[]
                {
                    new { Name = "monkey-text-ready", Description = "Перевірка готовності тексту" },
                    new { Name = "word-counter", Description = "Підрахунок кількості слів" }
                }
            }
        };

        return Ok(mockAlgorithms);
    }

    /// <summary>
    /// Отримання JSON-схеми для вхідних даних конкретного алгоритму (для побудови UI)
    /// Запит: GET /api/meta/input/{category}/{algorithm}
    /// </summary>
    [HttpGet("input/{category}/{algorithm}")]
    public IActionResult GetAlgorithmSchema(string category, string algorithm)
    {
        // Заглушка JSON-схеми, щоб фронтенд міг відмалювати форму на Canvas
        var mockSchema = new
        {
            Category = category,
            Algorithm = algorithm,
            Schema = new
            {
                type = "object",
                properties = new
                {
                    textInput = new { type = "string", title = "Вхідний текст" },
                    mode = new { type = "string", @enum = new[] { "fast", "accurate" }, title = "Режим роботи" }
                },
                required = new[] { "textInput" }
            }
        };

        return Ok(mockSchema);
    }
}