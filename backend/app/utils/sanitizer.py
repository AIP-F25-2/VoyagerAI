"""
Input sanitization utility to prevent XSS attacks
"""
import bleach
from html import unescape

# Allowed HTML tags for rich text content
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target']
}

def sanitize_html(text: str) -> str:
    """
    Sanitize HTML input to prevent XSS attacks.
    Allows only safe HTML tags and attributes.
    
    Args:
        text: HTML string to sanitize
        
    Returns:
        Sanitized HTML string
    """
    if not text:
        return ""
    
    # Decode HTML entities first
    text = unescape(str(text))
    
    # Sanitize HTML
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return cleaned.strip()

def sanitize_text(text: str) -> str:
    """
    Sanitize plain text input by removing all HTML tags.
    
    Args:
        text: Text string to sanitize
        
    Returns:
        Sanitized plain text string
    """
    if not text:
        return ""
    
    # Remove all HTML tags
    cleaned = bleach.clean(str(text), tags=[], strip=True)
    
    return cleaned.strip()

def sanitize_email(email: str) -> str:
    """
    Sanitize email address (basic validation and cleaning).
    
    Args:
        email: Email string to sanitize
        
    Returns:
        Sanitized email string (lowercased and stripped)
    """
    if not email:
        return ""
    
    return str(email).strip().lower()

def sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent malicious links.
    Only allows http and https protocols.
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL string or empty string if invalid
    """
    if not url:
        return ""
    
    url = str(url).strip()
    
    # Basic validation - must start with http:// or https://
    # Security Hotspot Review: This code checks if URLs start with 'http://' or 'https://' for validation.
    # This is NOT an insecure use of HTTP - it's a security check to ensure only valid HTTP/HTTPS URLs
    # are allowed. The function rejects invalid URLs and only accepts http:// or https:// protocols.
    if not (url.startswith('http://') or url.startswith('https://')):  # NOSONAR python:S5332 - URL validation check, not insecure use
        return ""
    
    # Clean the URL
    cleaned = bleach.clean(url, tags=[], strip=True)
    
    return cleaned

