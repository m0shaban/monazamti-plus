"""
Password validation utilities
"""
import re
import logging

logger = logging.getLogger(__name__)

# Common passwords to reject
COMMON_PASSWORDS = {
    'password', 'admin', '123456', 'qwerty', 'welcome', 'letmein',
    '12345678', 'password123', 'admin123', 'welcome123'
}

def validate_password_strength(password, username=None, email=None):
    """
    Validate password strength against common patterns and username/email
    
    Args:
        password (str): The password to check
        username (str, optional): Username to check against
        email (str, optional): Email to check against
    
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    # Check for minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    # Check for maximum length (to prevent DoS attacks)
    if len(password) > 128:
        return False, "Password is too long. Maximum length is 128 characters."
    
    # Check for common passwords
    if password.lower() in COMMON_PASSWORDS:
        return False, "This is a commonly used password and is not secure."
    
    # Check for username or email in password
    if username and username.lower() in password.lower():
        return False, "Password cannot contain your username."
    
    if email and email.split('@')[0].lower() in password.lower():
        return False, "Password cannot contain your email address."
    
    # Check for complexity (at least one letter and one number)
    if not (re.search(r'[A-Za-z]', password) and re.search(r'\d', password)):
        return False, "Password must contain both letters and numbers."
    
    # Password appears to be valid
    return True, ""
