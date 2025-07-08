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
- **Multi-language Support**: Internationalization with EN, ID, JP, KO, CN languages
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

### Language Support
- `GET /api/v1/languages` - Get supported languages with localized names
- `GET /api/v1/language/current` - Get current language information
- `GET /api/v1/language/test` - Test language translations

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

## Language Support

The API supports internationalization with the following languages:
- **English (en)** - Default language
- **Indonesian (id)** - Bahasa Indonesia
- **Japanese (jp)** - 日本語
- **Korean (ko)** - 한국어
- **Chinese (cn)** - 中文

### Language API Endpoints
- `GET /api/v1/languages` - Get supported languages
- `GET /api/v1/language/current` - Get current language info
- `GET /api/v1/language/test` - Test language translations

### Language Headers
- `Accept-Language: en,id;q=0.9,jp;q=0.8` - Standard language preference
- `X-Language: id` - Force specific language

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url VARCHAR(255),
    bio TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP
);
```

#### chats
```sql
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    chat_type VARCHAR(20) DEFAULT 'private', -- private, group
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### messages
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id),
    sender_id UUID REFERENCES users(id),
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text', -- text, image, video, file, sticker
    file_url VARCHAR(255),
    file_name VARCHAR(255),
    file_size INTEGER,
    reply_to_id INTEGER REFERENCES messages(id),
    is_edited BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### chat_participants
```sql
CREATE TABLE chat_participants (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'member', -- admin, member
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    UNIQUE(chat_id, user_id)
);
```

### Video Call Tables

#### video_calls
```sql
CREATE TABLE video_calls (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR(255) UNIQUE NOT NULL,
    call_type VARCHAR(20) DEFAULT 'video', -- video, audio
    status VARCHAR(20) DEFAULT 'initiated', -- initiated, ongoing, ended
    initiated_by UUID REFERENCES users(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration INTEGER -- seconds
);
```

#### call_participants
```sql
CREATE TABLE call_participants (
    id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES video_calls(id),
    user_id UUID REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    UNIQUE(call_id, user_id)
);
```

### Push Notification Tables

#### device_tokens
```sql
CREATE TABLE device_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(20), -- ios, android, web
    device_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### push_notifications
```sql
CREATE TABLE push_notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    notification_type VARCHAR(50), -- message, call, system
    category VARCHAR(50),
    data JSONB,
    is_sent BOOLEAN DEFAULT false,
    fcm_message_id VARCHAR(255),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);
```

### Location Tables

#### user_locations
```sql
CREATE TABLE user_locations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    accuracy DECIMAL(6, 2),
    altitude DECIMAL(8, 2),
    speed DECIMAL(6, 2),
    heading DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### location_shares
```sql
CREATE TABLE location_shares (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    target_user_id UUID REFERENCES users(id), -- NULL for public share
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### geofence_areas
```sql
CREATE TABLE geofence_areas (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    center_latitude DECIMAL(10, 7) NOT NULL,
    center_longitude DECIMAL(10, 7) NOT NULL,
    radius_meters INTEGER NOT NULL,
    notify_on_entry BOOLEAN DEFAULT true,
    notify_on_exit BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### geofence_events
```sql
CREATE TABLE geofence_events (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    geofence_id INTEGER REFERENCES geofence_areas(id),
    event_type VARCHAR(20), -- entry, exit
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## External Service Schemas

### AWS S3 Configuration

#### Bucket Structure
```
your-bucket-name/
├── avatars/
│   ├── {user_id}/
│   │   ├── original.jpg
│   │   └── thumbnail.jpg
├── chat-files/
│   ├── {chat_id}/
│   │   ├── {file_id}.{ext}
│   │   └── thumbnails/
│   │       └── {file_id}_thumb.jpg
├── stickers/
│   ├── packs/
│   │   └── {pack_id}/
│   │       └── {sticker_id}.{ext}
└── temp/
    └── {upload_id}.{ext}
```

#### S3 Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/public/*"
    },
    {
      "Sid": "AuthenticatedUpload",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:user/nerutalk-api"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

### Firebase Cloud Messaging (FCM)

#### Service Account JSON Structure
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxx@your-project-id.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
```

#### FCM Message Payload Structure
```json
{
  "message": {
    "token": "device-token",
    "notification": {
      "title": "Message Title",
      "body": "Message Body"
    },
    "data": {
      "type": "message",
      "chat_id": "123",
      "sender_id": "user-id"
    },
    "android": {
      "notification": {
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "sound": "default"
      }
    },
    "apns": {
      "payload": {
        "aps": {
          "sound": "default",
          "badge": 1
        }
      }
    }
  }
}
```

### Agora.io Video Calls

#### Channel Configuration
```javascript
{
  "appId": "your-agora-app-id",
  "channel": "unique-channel-name",
  "token": "generated-rtc-token",
  "uid": 12345,
  "role": "host", // host or audience
  "privilege": {
    "joinChannel": true,
    "publishStream": true
  },
  "expireTime": 86400 // 24 hours in seconds
}
```

#### WebRTC Configuration
```json
{
  "iceServers": [
    {
      "urls": "stun:stun.agora.io"
    },
    {
      "urls": "turn:turn.agora.io",
      "username": "username",
      "credential": "password"
    }
  ],
  "iceCandidatePoolSize": 10
}
```

### WebSocket Connection Schema

#### Connection Handshake
```
ws://localhost:8000/ws?token=jwt-token
```

#### Message Format
```json
{
  "type": "message_type",
  "data": {
    "key": "value"
  },
  "timestamp": "2025-01-01T00:00:00Z",
  "language": "en"
}
```

#### Event Types
```typescript
interface WebSocketMessage {
  type: 'join_chat' | 'leave_chat' | 'typing_indicator' | 'message_read' |
        'call_initiated' | 'call_answered' | 'call_declined' | 'call_ended' |
        'location_update' | 'location_share_start' | 'location_share_stop';
  data: any;
  timestamp?: string;
  language?: string;
}
```

### Redis Schema

#### Cache Keys Structure
```
nerutalk:
├── sessions:{user_id} -> session_data
├── chat_typing:{chat_id} -> {user_id: timestamp}
├── user_status:{user_id} -> online|offline|away
├── call_tokens:{call_id} -> agora_token
├── rate_limit:{ip}:{endpoint} -> request_count
└── location_cache:{user_id} -> location_data
```

#### Session Data Structure
```json
{
  "user_id": "uuid",
  "username": "string",
  "last_activity": "timestamp",
  "device_info": {
    "type": "mobile|web|desktop",
    "os": "ios|android|windows|macos|linux",
    "version": "app_version"
  },
  "language": "en|id|jp|ko|cn"
}
```

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

#### Language & Internationalization
```env
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,id,jp,ko,cn
AUTO_DETECT_LANGUAGE=true
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
