from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.files import router as files_router
from app.api.v1.media import router as media_router
from app.api.v1.video_calls import router as video_calls_router
from app.api.v1.push_notifications import router as push_notifications_router
from app.api.v1.location import router as location_router
from app.websocket.websocket_handler import websocket_endpoint, cleanup_typing_indicators
import asyncio

# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for NeruTalk chat application",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(video_calls_router, prefix="/api/v1")
app.include_router(push_notifications_router, prefix="/api/v1")
app.include_router(location_router, prefix="/api/v1", tags=["location"])

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Welcome to NeruTalk Backend API",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy", "service": settings.app_name}


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    Start background tasks.
    """
    # Start background task for cleaning up typing indicators
    asyncio.create_task(cleanup_typing_indicators())
