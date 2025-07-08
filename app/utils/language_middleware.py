"""
Language middleware for handling internationalization in FastAPI.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.utils.language import get_language_from_header, SupportedLanguage, DEFAULT_LANGUAGE
import logging

logger = logging.getLogger(__name__)


class LanguageMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and set user language from Accept-Language header."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and detect language from headers.
        
        Args:
            request (Request): Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response: HTTP response
        """
        # Get language from Accept-Language header
        accept_language = request.headers.get("Accept-Language", "")
        detected_language = get_language_from_header(accept_language)
        
        # Also check for custom X-Language header for explicit language setting
        custom_language = request.headers.get("X-Language", "").lower()
        if custom_language:
            try:
                detected_language = SupportedLanguage(custom_language)
            except ValueError:
                # Invalid language code, use detected language
                logger.warning(f"Invalid language code in X-Language header: {custom_language}")
        
        # Store language in request state
        request.state.language = detected_language
        
        # Process request
        response = await call_next(request)
        
        # Add language to response headers for client information
        response.headers["X-Content-Language"] = detected_language.value
        
        return response


def get_request_language(request: Request) -> SupportedLanguage:
    """
    Get the detected language from request state.
    
    Args:
        request (Request): FastAPI request object
    
    Returns:
        SupportedLanguage: Detected or default language
    """
    return getattr(request.state, 'language', DEFAULT_LANGUAGE)


# Dependency function for FastAPI endpoints
def get_language_dependency():
    """
    FastAPI dependency to get current request language.
    
    Returns:
        function: Dependency function
    """
    def _get_language(request: Request) -> SupportedLanguage:
        return get_request_language(request)
    
    return _get_language


# Global language dependency
get_current_language = get_language_dependency()
