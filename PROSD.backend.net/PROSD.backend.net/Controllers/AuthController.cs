using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using PROSD.backend.net.Data;
using PROSD.backend.net.Dtos;
using PROSD.backend.net.Models;
using PROSD.backend.net.Services;

namespace PROSD.backend.net.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly AppDbContext _dbContext;
    private readonly ILogger<AuthController> _logger;

    public AuthController(AppDbContext dbContext, ILogger<AuthController> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    [HttpPost("register")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Register([FromBody] RegisterUserRequest request)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var normalizedEmail = request.Email.Trim().ToLowerInvariant();

        var exists = await _dbContext.Users.AnyAsync(u => u.Email == normalizedEmail);
        if (exists)
        {
            return Conflict(new { message = "Email already registered." });
        }

        var user = new UserAccount
        {
            Email = normalizedEmail,
            PasswordHash = PasswordHasher.HashPassword(request.Password),
            CreatedAt = DateTime.UtcNow
        };

        _dbContext.Users.Add(user);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("User registered: {UserId}", user.Id);

        var response = new RegisterUserResponse
        {
            Id = user.Id,
            Email = user.Email
        };

        return Ok(response);
    }
}
