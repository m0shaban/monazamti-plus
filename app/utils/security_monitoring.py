"""
Security monitoring utilities for the application
"""
import logging
import json
from datetime import datetime
from flask import request, current_app
import os

logger = logging.getLogger(__name__)

# Set up a dedicated security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Create a file handler for security events if not already set up
if not security_logger.handlers:
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        security_log_file = os.path.join(log_dir, 'security.log')
        file_handler = logging.FileHandler(security_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to the security logger
        security_logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Error setting up security logging: {e}")

def log_security_event(event_type, details, severity="INFO"):
    """
    Log a security-related event
    
    Args:
        event_type (str): The type of event (login_attempt, password_change, etc.)
        details (dict): Details about the event
        severity (str): Severity level (INFO, WARNING, ERROR, CRITICAL)
    """
    # Create the log entry
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else "Unknown",
        'details': details,
        'severity': severity
    }
    
    # Add current user if authenticated
    from flask_login import current_user
    if current_user and current_user.is_authenticated:
        log_entry['user_id'] = current_user.id
        log_entry['username'] = current_user.username
    
    # Log based on severity
    log_method = getattr(security_logger, severity.lower(), security_logger.info)
    log_method(json.dumps(log_entry))
    
    return log_entry

def detect_suspicious_activity(user_id, event_type, threshold=5):
    """
    Basic detection of suspicious activity based on frequency
    
    Args:
        user_id: User identifier
        event_type: Type of event to check
        threshold: Number of events to trigger alert
    
    Returns:
        bool: True if suspicious activity detected
    """
    # In a production app, this would query a database or log analyzer
    # For this example, we'll just log the check
    security_logger.info(f"Checking for suspicious {event_type} activity for user {user_id}")
    
    # Always return False for this simplified implementation
    return False
