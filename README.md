# NeruTalk Backend

A comprehensive backend API for a modern chat application built with FastAPI, featuring real-time messaging, video calls, file sharing, push notifications, and location tracking with geofencing.

## Features

### Core Features
- **Authentication & Authorization**: JWT-based authentication with refresh tokens
- **Real-time Chat**: WebSocket-based messaging with typing indicators and read receipts
- **Video Calling**: Integration with Agora.io for high-quality video/audio calls
- **File Sharing**: Support for images, videos, documents, stickers, and GIFs
- **User Profiles**: Comprehensive user management with avatars and settings

### Advanced Features
- **Push Notifications**: FCM-based cross-platform push notifications with templates
- **Location Tracking**: GPS-based location sharing with privacy controls
- **Geofencing**: Create virtual boundaries with entry/exit notifications
- **Nearby Users**: Discover users within a specified radius
- **Location History**: Track and view location history with time-based queries
- **Real-time Updates**: Live location sharing via WebSocket

### System Features
- **Clean Architecture**: Well-structured, maintainable codebase following SOLID principles
- **Scalable Design**: Repository pattern with service layer abstraction
- **Comprehensive API**: RESTful APIs with automatic OpenAPI documentation
- **WebSocket Support**: Real-time communication for chat, calls, and location updates
- **Security**: Environment-based configuration with secure token handling
- **Database Migrations**: Alembic-based database version control

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and sessions
- **Authentication**: JWT with bcrypt password hashing
- **Real-time**: WebSockets for live messaging and location updates
- **File Storage**: AWS S3 integration with thumbnail generation
- **Background Tasks**: Celery with Redis broker
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Video Calls**: Agora.io SDK integration
- **API Documentation**: Automatic OpenAPI/Swagger docs
- **Containerization**: Docker and Docker Compose support

## API Endpoints

### Authentication
- `POST /api/v1/register` - User registration
- `POST /api/v1/login` - User login
- `POST /api/v1/logout` - User logout
- `POST /api/v1/refresh-token` - Refresh access token
- `GET /api/v1/profile` - Get user profile
- `PUT /api/v1/profile` - Update user profile
- `POST /api/v1/upload-avatar` - Upload user avatar

### Chat & Messaging
- `GET /api/v1/chats` - Get user's chats
- `POST /api/v1/chats` - Create new chat
- `GET /api/v1/chats/{chat_id}` - Get chat details
- `POST /api/v1/chats/{chat_id}/messages` - Send message
- `GET /api/v1/chats/{chat_id}/messages` - Get chat messages
- `PUT /api/v1/messages/{message_id}/read` - Mark message as read
- `POST /api/v1/chats/{chat_id}/participants` - Add chat participant
- `DELETE /api/v1/chats/{chat_id}/participants/{user_id}` - Remove participant

### Video Calls
- `POST /api/v1/video-calls/initiate` - Initiate video call
- `POST /api/v1/video-calls/{call_id}/answer` - Answer call
- `POST /api/v1/video-calls/{call_id}/decline` - Decline call
- `POST /api/v1/video-calls/{call_id}/end` - End call
- `GET /api/v1/video-calls/history` - Get call history
- `GET /api/v1/video-calls/stats` - Get call statistics
- `POST /api/v1/video-calls/{call_id}/participants` - Add call participant

### File & Media
- `POST /api/v1/files/upload` - Upload file
- `GET /api/v1/files/{file_id}` - Download file
- `DELETE /api/v1/files/{file_id}` - Delete file
- `GET /api/v1/media/stickers` - Get available stickers
- `GET /api/v1/media/gifs/search` - Search GIFs
- `GET /api/v1/media/gifs/trending` - Get trending GIFs

### Push Notifications
- `POST /api/v1/push-notifications/device-tokens` - Register device token
- `PUT /api/v1/push-notifications/device-tokens/{token_id}` - Update device token
- `DELETE /api/v1/push-notifications/device-tokens/{token_id}` - Remove device token
- `GET /api/v1/push-notifications/device-tokens` - Get user's device tokens
- `POST /api/v1/push-notifications/send` - Send notification to users
- `POST /api/v1/push-notifications/broadcast` - Broadcast notification
- `GET /api/v1/push-notifications/stats` - Get notification statistics

### Location Tracking
- `POST /api/v1/location/update` - Update current location
- `GET /api/v1/location/current` - Get own current location
- `GET /api/v1/location/current/{user_id}` - Get user's location (if shared)
- `GET /api/v1/location/history` - Get own location history
- `GET /api/v1/location/history/{user_id}` - Get user's location history
- `GET /api/v1/location/nearby` - Find nearby users
- `GET /api/v1/location/stats` - Get location statistics

### Location Sharing
- `POST /api/v1/location/shares` - Create location share
- `GET /api/v1/location/shares` - Get active location shares
- `PUT /api/v1/location/shares/{share_id}` - Update location share
- `DELETE /api/v1/location/shares/{share_id}` - Stop location sharing

### Geofencing
- `POST /api/v1/location/geofences` - Create geofence area
- `GET /api/v1/location/geofences` - Get user's geofence areas
- `PUT /api/v1/location/geofences/{geofence_id}` - Update geofence area
- `DELETE /api/v1/location/geofences/{geofence_id}` - Delete geofence area
- `GET /api/v1/location/geofences/events` - Get geofence events

## WebSocket Events

### Chat Events
- `join_chat` - Join a chat room
- `leave_chat` - Leave a chat room
- `typing_indicator` - Send typing status
- `message_read` - Mark message as read

### Call Events
- `call_initiated` - Call started
- `call_answered` - Call answered
- `call_declined` - Call declined
- `call_ended` - Call ended
- `call_participant_joined` - Participant joined call
- `call_participant_left` - Participant left call

### Location Events
- `location_update` - Real-time location update
- `location_share_start` - Start sharing location
- `location_share_stop` - Stop sharing location
- `shared_location_update` - Receive shared location update
- `geofence_event` - Geofence entry/exit notification

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nerutalk-backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

Configure the following environment variables in your `.env` file:

#### Core Application
```env
APP_NAME=NeruTalk Backend API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-super-secret-key-here
```

#### Database Configuration
```env
DATABASE_URL=postgresql://username:password@localhost:5432/nerutalk_db
REDIS_URL=redis://localhost:6379/0
```

#### JWT Authentication
```env
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### File Storage (AWS S3)
```env
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov,pdf,doc,docx
```

#### Push Notifications (Firebase)
```env
FCM_SERVER_KEY=your-firebase-server-key
FCM_PROJECT_ID=your-firebase-project-id
```

#### Video Calls (Agora.io)
```env
AGORA_APP_ID=your-agora-app-id
AGORA_APP_CERTIFICATE=your-agora-app-certificate
AGORA_TOKEN_EXPIRY_HOURS=24
```

#### External APIs
```env
GIPHY_API_KEY=your-giphy-api-key
TENOR_API_KEY=your-tenor-api-key
```

#### Security & CORS
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
TRUSTED_HOSTS=localhost,127.0.0.1
```

#### Background Tasks
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Setup

1. Run with Docker Compose:
```bash
docker-compose up -d
```

This will start PostgreSQL, Redis, and the FastAPI application.

## Project Structure

```
nerutalk-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── auth.py          # Authentication endpoints
│   ├── core/
│   │   ├── config.py            # Application configuration
│   │   ├── database.py          # Database setup
│   │   └── security.py          # Security utilities
│   ├── models/
│   │   └── user.py              # Database models
│   ├── repositories/
│   │   └── user_repository.py   # Data access layer
│   ├── schemas/
│   │   └── auth.py              # Pydantic schemas
│   ├── services/
│   │   └── auth_service.py      # Business logic
│   ├── utils/                   # Utility functions
│   ├── websocket/               # WebSocket handlers
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
├── tests/                       # Test files
├── requirements.txt             # Python dependencies
├── docker-compose.yml          # Docker configuration
├── Dockerfile                   # Docker image
└── .env.example                # Environment variables template
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Workflow

### Feature Development

1. Create a feature branch:
```bash
git checkout dev
git pull origin dev
git checkout -b feat/feature-name
```

2. Make your changes following the established patterns
3. Test your changes thoroughly
4. Commit with clear, professional commit messages
5. Push and create a pull request to `dev` branch

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Add new table"
```

Apply migrations:
```bash
alembic upgrade head
```

### Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app
```

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `AWS_ACCESS_KEY_ID`: AWS S3 access key
- `FIREBASE_SERVER_KEY`: Firebase push notification key

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new features
3. Update documentation as needed
4. Use clear, descriptive commit messages
5. Ensure all tests pass before submitting PR

## License

This project is proprietary and confidential.
