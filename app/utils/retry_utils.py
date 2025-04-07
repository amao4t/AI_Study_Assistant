
import time
import logging
import functools
import requests
from typing import Callable, Any, Optional, List, Dict

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def with_retry(max_retries: int = 3, 
               base_delay: float = 1.0, 
               backoff_factor: float = 2.0,
               retry_on_exceptions: List[type] = None) -> Callable:
    """
    Decorator that implements retry logic for API calls.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier applied to delay for each retry
        retry_on_exceptions: List of exception types to retry on (defaults to requests.exceptions.RequestException)
    
    Returns:
        Decorated function with retry logic
    """
    if retry_on_exceptions is None:
        retry_on_exceptions = [
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            delay = base_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except tuple(retry_on_exceptions) as e:
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(f"Maximum retries ({max_retries}) exceeded for {func.__name__}. Last error: {str(e)}")
                        raise APIError(
                            message=f"Failed after {max_retries} retries: {str(e)}",
                            details={"original_exception": str(e), "function": func.__name__}
                        )
                    
                    # Log the retry attempt
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after error: {str(e)}. "
                        f"Waiting {delay:.2f}s before next attempt."
                    )
                    
                    # Wait before retrying
                    time.sleep(delay)
                    
                    # Increase the delay for the next retry using exponential backoff
                    delay *= backoff_factor
        
        return wrapper
    
    return decorator


def get_default_fallback_response(service_name: str) -> Dict:
    """
    Generate a standard fallback response when API services are unavailable
    
    Args:
        service_name: Name of the service that failed
        
    Returns:
        A default response object
    """
    return {
        "error": True,
        "service_unavailable": True,
        "message": f"The {service_name} service is currently unavailable. Please try again later.",
        "fallback": True
    }