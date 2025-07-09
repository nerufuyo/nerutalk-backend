"""
Example implementation showing how to use the language system in API endpoints.
This file demonstrates best practices for internationalization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.utils.language import get_text, SupportedLanguage
from app.utils.language_middleware import get_current_language

router = APIRouter()


@router.post("/example/create")
async def create_example_with_language(
    name: str,
    current_user: User = Depends(get_current_user),
    language: SupportedLanguage = Depends(get_current_language),
    db: Session = Depends(get_db)
):
    """
    Example endpoint showing how to use language system.
    
    This endpoint demonstrates:
    1. Getting current language from middleware
    2. Using get_text() for internationalized responses
    3. Formatting messages with parameters
    4. Handling errors with localized messages
    """
    try:
        # Simulate some business logic
        if not name or len(name.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_text("validation_error", language)
            )
        
        # Simulate successful creation
        # In real implementation, you would create the resource here
        
        return {
            "message": get_text("operation_successful", language),
            "success_message": get_text("data_saved", language),
            "data": {
                "name": name,
                "created_by": current_user.username
            },
            "language": language.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_text("internal_server_error", language)
        )


@router.get("/example/user-greeting")
async def get_user_greeting(
    current_user: User = Depends(get_current_user),
    language: SupportedLanguage = Depends(get_current_language)
):
    """
    Example showing how to create personalized messages with language support.
    """
    # Create greeting based on time of day (simplified example)
    import datetime
    
    hour = datetime.datetime.now().hour
    
    if hour < 12:
        greeting_key = "good_morning"
    elif hour < 18:
        greeting_key = "good_afternoon"
    else:
        greeting_key = "good_evening"
    
    # You could add these to the language.py translations
    greeting_translations = {
        "good_morning": {
            "en": "Good morning, {name}!",
            "id": "Selamat pagi, {name}!",
            "jp": "おはよう、{name}さん！",
            "ko": "좋은 아침, {name}님!",
            "cn": "早上好，{name}！"
        },
        "good_afternoon": {
            "en": "Good afternoon, {name}!",
            "id": "Selamat siang, {name}!",
            "jp": "こんにちは、{name}さん！",
            "ko": "좋은 오후, {name}님!",
            "cn": "下午好，{name}！"
        },
        "good_evening": {
            "en": "Good evening, {name}!",
            "id": "Selamat malam, {name}!",
            "jp": "こんばんは、{name}さん！",
            "ko": "좋은 저녁, {name}님!",
            "cn": "晚上好，{name}！"
        }
    }
    
    greeting_text = greeting_translations[greeting_key].get(
        language.value, 
        greeting_translations[greeting_key]["en"]
    )
    
    return {
        "greeting": greeting_text.format(name=current_user.display_name or current_user.username),
        "language": language.value,
        "time": datetime.datetime.now().isoformat()
    }


# Usage in other services:
"""
# In any service class, you can use language like this:

class ChatService:
    def send_message(self, message_data, language: SupportedLanguage):
        try:
            # ... business logic ...
            
            return {
                "message": get_text("message_sent", language),
                "data": message_data
            }
        except Exception:
            raise Exception(get_text("internal_server_error", language))

# In notification service:
class PushNotificationService:
    def send_notification(self, user_id: int, message_key: str, language: SupportedLanguage, **kwargs):
        title = get_text(f"{message_key}_title", language, **kwargs)
        body = get_text(f"{message_key}_body", language, **kwargs)
        
        # Send notification with localized content
        return self.fcm_service.send(title=title, body=body)

# Client usage examples:

# 1. Using Accept-Language header (automatic detection):
curl -H "Accept-Language: id,en;q=0.9" http://localhost:8000/api/v1/example/create

# 2. Using X-Language header (explicit language):
curl -H "X-Language: jp" http://localhost:8000/api/v1/example/create

# 3. JavaScript fetch example:
fetch('/api/v1/example/create', {
    headers: {
        'X-Language': 'ko',
        'Content-Type': 'application/json'
    }
})
"""
