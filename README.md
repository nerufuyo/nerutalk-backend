# NeruTalk Backend

A comprehensive backend API for a modern chat application built with FastAPI, featuring real-time messaging, video calls, file sharing, and location tracking.

## Features

- **Authentication & Authorization**: JWT-based authentication with refresh tokens
- **Real-time Chat**: WebSocket-based messaging system
- **Video Calling**: Integration with video call services (Agora.io/Twilio)
- **File Sharing**: Support for images, videos, stickers, and GIFs
- **User Profiles**: Comprehensive user management and profiles
- **Push Notifications**: Cross-platform push notifications
- **Location Tracking**: GPS-based location sharing
- **Clean Architecture**: Well-structured, maintainable codebase

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and sessions
- **Authentication**: JWT with bcrypt password hashing
- **Real-time**: WebSockets for live messaging
- **File Storage**: AWS S3 or Cloudinary integration
- **Background Tasks**: Celery with Redis broker
- **API Documentation**: Automatic OpenAPI/Swagger docs

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
