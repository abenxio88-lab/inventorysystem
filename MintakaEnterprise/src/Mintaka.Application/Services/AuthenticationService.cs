namespace Mintaka.Application.Services;

using Mintaka.Core.Entities;
using Mintaka.Core.Interfaces;
using Microsoft.Extensions.Logging;
using System.Security.Cryptography;

/// <summary>
/// Authentication and user management service with security best practices
/// </summary>
public class AuthenticationService : IAuthenticationService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ILogger<AuthenticationService> _logger;
    private readonly int _maxFailedAttempts = 5;
    private readonly TimeSpan _lockoutDuration = TimeSpan.FromMinutes(30);

    public AuthenticationService(IUnitOfWork unitOfWork, ILogger<AuthenticationService> logger)
    {
        _unitOfWork = unitOfWork;
        _logger = logger;
    }

    /// <summary>
    /// Authenticate user with username and password
    /// </summary>
    public async Task<AuthResult> LoginAsync(string username, string password, string? ipAddress = null)
    {
        try
        {
            // Get user by username
            var user = await _unitOfWork.Users.GetByUsernameAsync(username);
            
            if (user == null)
            {
                _logger.LogWarning("Login attempt for non-existent user: {Username}", username);
                return AuthResult.FailureResult("Invalid username or password");
            }

            // Check if account is locked
            if (user.IsLocked && user.LockedUntil.HasValue && user.LockedUntil.Value > DateTime.UtcNow)
            {
                var remainingLockout = user.LockedUntil.Value - DateTime.UtcNow;
                return AuthResult.FailureResult($"Account is locked. Try again in {(int)remainingLockout.TotalMinutes} minutes.");
            }

            // Reset lock if lockout period has expired
            if (user.IsLocked && (!user.LockedUntil.HasValue || user.LockedUntil.Value <= DateTime.UtcNow))
            {
                user.IsLocked = false;
                user.FailedLoginAttempts = 0;
                user.LockedUntil = null;
                await _unitOfWork.Users.UpdateAsync(user);
            }

            // Verify password
            var isValidPassword = VerifyPassword(password, user.PasswordHash, user.Salt);
            
            if (!isValidPassword)
            {
                // Increment failed attempts
                user.FailedLoginAttempts++;
                
                if (user.FailedLoginAttempts >= _maxFailedAttempts)
                {
                    user.IsLocked = true;
                    user.LockedUntil = DateTime.UtcNow + _lockoutDuration;
                    await _unitOfWork.Users.UpdateAsync(user);
                    
                    _logger.LogWarning("Account locked due to multiple failed attempts: {Username}", username);
                    return AuthResult.FailureResult("Too many failed attempts. Account locked for 30 minutes.");
                }
                
                await _unitOfWork.Users.UpdateAsync(user);
                await _unitOfWork.SaveChangesAsync();
                
                _logger.LogWarning("Failed login attempt for user: {Username} (Attempt {Attempt})", 
                    username, user.FailedLoginAttempts);
                
                return AuthResult.FailureResult("Invalid username or password");
            }

            // Successful login
            user.FailedLoginAttempts = 0;
            user.IsLocked = false;
            user.LockedUntil = null;
            user.LastLoginAt = DateTime.UtcNow;
            await _unitOfWork.Users.UpdateAsync(user);
            await _unitOfWork.Users.UpdateLastLoginAsync(user.Id);
            await _unitOfWork.SaveChangesAsync();

            // Create audit log
            var auditLog = new AuditLog
            {
                TableName = "Users",
                RecordId = user.Id,
                Action = "Login",
                OldValues = string.Empty,
                NewValues = $"IpAddress: {ipAddress ?? "Unknown"}",
                UserId = user.Id,
                TenantId = user.TenantId,
                Timestamp = DateTime.UtcNow
            };
            await _unitOfWork.AuditLogs.AddAsync(auditLog);
            await _unitOfWork.SaveChangesAsync();

            _logger.LogInformation("User logged in successfully: {Username}", username);

            return AuthResult.SuccessResult(user);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during login for user: {Username}", username);
            return AuthResult.FailureResult("An error occurred during authentication.");
        }
    }

    /// <summary>
    /// Register a new user
    /// </summary>
    public async Task<AuthResult> RegisterAsync(string username, string email, string password, string role, int tenantId, int createdBy)
    {
        try
        {
            // Validate input
            if (string.IsNullOrWhiteSpace(username) || username.Length < 3)
                return AuthResult.FailureResult("Username must be at least 3 characters.");

            if (string.IsNullOrWhiteSpace(email) || !IsValidEmail(email))
                return AuthResult.FailureResult("Invalid email address.");

            if (string.IsNullOrWhiteSpace(password) || password.Length < 8)
                return AuthResult.FailureResult("Password must be at least 8 characters.");

            // Check if username exists
            var usernameExists = await _unitOfWork.Users.IsUsernameTakenAsync(username, tenantId);
            if (usernameExists)
                return AuthResult.FailureResult("Username already exists.");

            // Check if email exists
            var emailExists = await _unitOfWork.Users.IsEmailTakenAsync(email, tenantId);
            if (emailExists)
                return AuthResult.FailureResult("Email already registered.");

            // Hash password
            var salt = GenerateSalt();
            var passwordHash = HashPassword(password, salt);

            var user = new User
            {
                Username = username,
                Email = email,
                PasswordHash = passwordHash,
                Salt = salt,
                Role = role,
                TenantId = tenantId,
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            };

            await _unitOfWork.Users.AddAsync(user);
            await _unitOfWork.SaveChangesAsync();

            // Create audit log
            var auditLog = new AuditLog
            {
                TableName = "Users",
                RecordId = user.Id,
                Action = "Create",
                OldValues = string.Empty,
                NewValues = System.Text.Json.JsonSerializer.Serialize(new { user.Username, user.Email, user.Role }),
                UserId = createdBy,
                TenantId = tenantId,
                Timestamp = DateTime.UtcNow
            };
            await _unitOfWork.AuditLogs.AddAsync(auditLog);
            await _unitOfWork.SaveChangesAsync();

            _logger.LogInformation("New user registered: {Username} ({Email})", username, email);

            return AuthResult.SuccessResult(user);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error registering user: {Username}", username);
            return AuthResult.FailureResult("An error occurred during registration.");
        }
    }

    /// <summary>
    /// Change user password
    /// </summary>
    public async Task<bool> ChangePasswordAsync(int userId, string currentPassword, string newPassword)
    {
        try
        {
            var user = await _unitOfWork.Users.GetByIdAsync(userId);
            if (user == null)
                return false;

            // Verify current password
            if (!VerifyPassword(currentPassword, user.PasswordHash, user.Salt))
                return false;

            // Validate new password
            if (string.IsNullOrWhiteSpace(newPassword) || newPassword.Length < 8)
                return false;

            // Hash new password
            var newSalt = GenerateSalt();
            var newPasswordHash = HashPassword(newPassword, newSalt);

            user.PasswordHash = newPasswordHash;
            user.Salt = newSalt;

            await _unitOfWork.Users.UpdateAsync(user);
            await _unitOfWork.SaveChangesAsync();

            // Create audit log
            var auditLog = new AuditLog
            {
                TableName = "Users",
                RecordId = userId,
                Action = "PasswordChange",
                OldValues = string.Empty,
                NewValues = "Password changed",
                UserId = userId,
                TenantId = user.TenantId,
                Timestamp = DateTime.UtcNow
            };
            await _unitOfWork.AuditLogs.AddAsync(auditLog);
            await _unitOfWork.SaveChangesAsync();

            _logger.LogInformation("Password changed for user: {Username}", user.Username);

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error changing password for user: {UserId}", userId);
            return false;
        }
    }

    /// <summary>
    /// Reset failed login attempts (admin function)
    /// </summary>
    public async Task<bool> ResetFailedAttemptsAsync(string username, int adminUserId)
    {
        var user = await _unitOfWork.Users.GetByUsernameAsync(username);
        if (user == null)
            return false;

        user.FailedLoginAttempts = 0;
        user.IsLocked = false;
        user.LockedUntil = null;

        await _unitOfWork.Users.UpdateAsync(user);
        await _unitOfWork.Users.ResetFailedLoginAttemptsAsync(username);
        await _unitOfWork.SaveChangesAsync();

        _logger.LogInformation("Failed login attempts reset for user: {Username} by admin: {AdminId}", username, adminUserId);

        return true;
    }

    /// <summary>
    /// Get user by ID
    /// </summary>
    public async Task<User?> GetUserByIdAsync(int id)
    {
        return await _unitOfWork.Users.GetByIdAsync(id);
    }

    /// <summary>
    /// Get all users for a tenant
    /// </summary>
    public async Task<IEnumerable<User>> GetUsersByTenantAsync(int tenantId)
    {
        var users = await _unitOfWork.Users.GetAllAsync();
        return users.Where(u => u.TenantId == tenantId && u.IsActive).OrderBy(u => u.Username).ToList();
    }

    /// <summary>
    /// Deactivate a user
    /// </summary>
    public async Task<bool> DeactivateUserAsync(int userId, int adminUserId)
    {
        var user = await _unitOfWork.Users.GetByIdAsync(userId);
        if (user == null)
            return false;

        user.IsActive = false;
        await _unitOfWork.Users.UpdateAsync(user);
        await _unitOfWork.SaveChangesAsync();

        _logger.LogInformation("User deactivated: {Username} by admin: {AdminId}", user.Username, adminUserId);

        return true;
    }

    #region Private Helper Methods

    /// <summary>
    /// Hash password using PBKDF2 with HMAC-SHA256
    /// </summary>
    private static string HashPassword(string password, byte[] salt)
    {
        using var pbkdf2 = new Rfc2898DeriveBytes(password, salt, 100000, HashAlgorithmName.SHA256);
        var hash = pbkdf2.GetBytes(32);
        return Convert.ToBase64String(hash);
    }

    /// <summary>
    /// Verify password against stored hash
    /// </summary>
    private static bool VerifyPassword(string password, string storedHash, byte[] salt)
    {
        var computedHash = HashPassword(password, salt);
        return computedHash == storedHash;
    }

    /// <summary>
    /// Generate cryptographically secure salt
    /// </summary>
    private static byte[] GenerateSalt()
    {
        var salt = new byte[32];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(salt);
        return salt;
    }

    /// <summary>
    /// Validate email format
    /// </summary>
    private static bool IsValidEmail(string email)
    {
        try
        {
            var addr = new System.Net.Mail.MailAddress(email);
            return addr.Address == email;
        }
        catch
        {
            return false;
        }
    }

    #endregion
}

/// <summary>
/// Authentication result wrapper
/// </summary>
public class AuthResult
{
    public bool Success { get; private set; }
    public string? Message { get; private set; }
    public User? User { get; private set; }

    public static AuthResult SuccessResult(User user) => new() { Success = true, User = user, Message = "Login successful" };
    public static AuthResult FailureResult(string message) => new() { Success = false, Message = message };
    
    // Backwards compatible factory methods
    public static AuthResult SuccessFactory(User user) => SuccessResult(user);
    public static AuthResult FailureFactory(string message) => FailureResult(message);
}

/// <summary>
/// Authentication service interface
/// </summary>
public interface IAuthenticationService
{
    Task<AuthResult> LoginAsync(string username, string password, string? ipAddress = null);
    Task<AuthResult> RegisterAsync(string username, string email, string password, string role, int tenantId, int createdBy);
    Task<bool> ChangePasswordAsync(int userId, string currentPassword, string newPassword);
    Task<bool> ResetFailedAttemptsAsync(string username, int adminUserId);
    Task<User?> GetUserByIdAsync(int id);
    Task<IEnumerable<User>> GetUsersByTenantAsync(int tenantId);
    Task<bool> DeactivateUserAsync(int userId, int adminUserId);
}
