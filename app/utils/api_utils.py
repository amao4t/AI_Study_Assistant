import logging
import json
from typing import Dict, Any, Tuple, Optional
from flask import jsonify

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Standardized API error class for consistent error handling"""
    def __init__(self, message: str, code: int = 400, details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_response(self):
        """Convert error to a Flask response"""
        response = {
            'error': self.message,
            'details': self.details
        }
        return jsonify(response), self.code
    
    @classmethod
    def from_exception(cls, exception: Exception, code: int = 500, default_message: str = None):
        """Create APIError from a standard exception"""
        message = default_message or str(exception)
        return cls(message, code, {'exception_type': exception.__class__.__name__})

def get_default_error_message(service_name: str) -> str:
    """Get default error message for service failures"""
    return f"Sorry, the {service_name} service is currently experiencing issues. Please try again later."

def safe_api_call(func, *args, service_name="API", fallback_func=None, **kwargs) -> Tuple[Any, bool, Optional[str]]:
    """
    Execute an API call safely with fallback option
    
    Args:
        func: The function to call
        *args: Arguments to pass to func
        service_name: Name of the service for error messages
        fallback_func: Function to call if main function fails
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Tuple of (result, is_fallback, error_message)
    """
    try:
        # Attempt main API call
        result = func(*args, **kwargs)
        return result, False, None
    except Exception as e:
        logger.exception(f"Error in {service_name} call: {str(e)}")
        
        # Generate error message
        error_message = str(e)
        
        # Try fallback if provided
        if fallback_func:
            try:
                logger.info(f"Using fallback for {service_name}")
                fallback_result = fallback_func(*args, **kwargs)
                return fallback_result, True, error_message
            except Exception as fallback_error:
                logger.exception(f"Fallback error in {service_name}: {str(fallback_error)}")
                return None, False, f"{error_message} (Fallback also failed)"
        
        return None, False, error_message

def log_api_access(service_name: str, success: bool, details: Dict = None):
    """Log API access for monitoring and security"""
    details = details or {}
    logger.info(f"API access: {service_name}, success: {success}, details: {json.dumps(details)}")