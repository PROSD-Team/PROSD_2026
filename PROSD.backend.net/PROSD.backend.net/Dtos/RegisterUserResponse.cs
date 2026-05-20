namespace PROSD.backend.net.Dtos;

public class RegisterUserResponse
{
    public Guid Id { get; set; }

    public string Email { get; set; } = string.Empty;
}
