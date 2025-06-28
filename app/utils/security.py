"""
Security utilities for Flask application
"""
import logging
import re
from functools import wraps
from flask import request, abort, current_app
from werkzeug.exceptions import BadRequest, HTTPException
import time

logger = logging.getLogger(__name__)

# Regex patterns for HTTP method, URL path, and protocol validation
VALID_HTTP_METHOD = re.compile(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$')
VALID_HTTP_PROTOCOL = re.compile(r'^HTTP/[0-9]\.[0-9]$')

def validate_request():
    """
    Validate the incoming HTTP request:
    - Check for valid HTTP method
    - Check for valid protocol version
    - Check for other potential malformed request indicators
    
    Returns:
        bool: True if request appears valid, False otherwise
    """
    # Validate HTTP method
    method = request.method
    if not VALID_HTTP_METHOD.match(method):
        logger.warning(f"Invalid HTTP method detected: {method} from IP: {request.remote_addr}")
        return False
    
    # Get protocol version through environ 
    server_protocol = request.environ.get('SERVER_PROTOCOL', '')
    if not VALID_HTTP_PROTOCOL.match(server_protocol):
        logger.warning(f"Invalid HTTP protocol detected: {server_protocol} from IP: {request.remote_addr}")
        return False
    
    return True

def request_validator():
    """
    Decorator to apply request validation to Flask endpoints.
    Usage: 
        @app.before_request
        @request_validator()
        def validate_before_request():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not validate_request():
                logger.warning(f"Request validation failed. Aborting request from: {request.remote_addr}")
                # Return 400 Bad Request for invalid requests
                abort(400, description="Invalid request format")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class RequestLogger:
    """
    Class to handle advanced request logging
    """
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with the Flask app"""
        self.app = app
        
        # Register before_request handler
        @app.before_request
        def log_request_info():
            request.start_time = time.time()
            
        # Register after_request handler
        @app.after_request
        def log_response_info(response):
            # Calculate request duration
            duration = time.time() - getattr(request, 'start_time', time.time())
            duration_ms = round(duration * 1000, 2)
            
            # Only log detailed information for unusual status codes
            if response.status_code >= 400 or response.status_code == 302:
                # Get protocol from environ
                protocol = request.environ.get('SERVER_PROTOCOL', 'UNKNOWN')
                
                # Log detailed information about the request and response
                logger.info(
                    f"Request: {request.method} {request.path} {protocol} | "
                    f"Response: {response.status_code} | "
                    f"IP: {request.remote_addr} | "
                    f"UserAgent: {request.user_agent.string if request.user_agent else 'UNKNOWN'} | "
                    f"Duration: {duration_ms}ms"
                )
            
            return response
