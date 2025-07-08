"""
Language API endpoints for internationalization support.
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
from app.utils.language import (
    SupportedLanguage, LANGUAGE_NAMES, get_text, DEFAULT_LANGUAGE
)
from app.utils.language_middleware import get_current_language

router = APIRouter()


@router.get("/languages", response_model=Dict[str, Any])
async def get_supported_languages(
    language: SupportedLanguage = Depends(get_current_language)
):
    """Get list of supported languages with localized names."""
    return {
        "supported_languages": [
            {
                "code": lang.value,
                "name": LANGUAGE_NAMES[lang][language.value],
                "native_name": LANGUAGE_NAMES[lang][lang.value]
            }
            for lang in SupportedLanguage
        ],
        "current_language": language.value,
        "default_language": DEFAULT_LANGUAGE.value
    }


@router.get("/language/current")
async def get_current_language_info(
    language: SupportedLanguage = Depends(get_current_language)
):
    """Get current language information."""
    return {
        "language": language.value,
        "name": LANGUAGE_NAMES[language][language.value],
        "native_name": LANGUAGE_NAMES[language][language.value],
        "is_default": language == DEFAULT_LANGUAGE
    }


@router.get("/language/test")
async def test_language_strings(
    language: SupportedLanguage = Depends(get_current_language)
):
    """Test endpoint to demonstrate language translations."""
    test_keys = [
        "auth_success",
        "login_success", 
        "message_sent",
        "call_initiated",
        "file_uploaded",
        "location_updated",
        "operation_successful"
    ]
    
    return {
        "language": language.value,
        "translations": {
            key: get_text(key, language)
            for key in test_keys
        }
    }
