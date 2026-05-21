# Staiz API - Hotel AI Chat Backend

A comprehensive FastAPI backend featuring AI-powered hotel search and booking assistance with chat tabs functionality, similar to ChatGPT's interface.

## Features

### 🔐 Authentication & User Management
- User registration with email and password
- JWT token-based authentication
- Password hashing with bcrypt
- User profile management

### 🤖 AI Chat System
- **LangChain Integration**: Advanced AI conversation capabilities
- **Hybrid Memory System**: Redis + MongoDB for optimal performance
- **Hotel Search AI**: Specialized AI for hotel recommendations and booking
- **Multi-Tool Support**: Database search, API calls, web scraping, vector search

### 💬 Chat Tabs Functionality
- **Multiple Conversation Threads**: Users can have multiple ongoing chats
- **Tab Management**: Create, rename, pin, reorder, and delete tabs
- **Session Isolation**: Each tab maintains its own conversation history
- **Persistent Storage**: All conversations stored in MongoDB
- **Real-time Updates**: Tab activity tracking and message counts

### 🏨 Hotel Search & Booking
- **Structured Hotel Data**: Complete hotel information with ratings, prices, amenities
- **Real-time Search**: Live hotel availability and pricing
- **Booking Integration**: Direct links to booking platforms
- **Location-based Search**: Geographic coordinates and mapping support
- **Advanced Filtering**: Star ratings, amenities, price ranges, cancellation policies

### 🛠️ Technical Features
- **MongoDB Integration**: Scalable document database
- **Redis Caching**: High-performance memory management
- **Vector Search**: Pinecone integration for semantic search
- **API Integration**: SerpAPI for hotel data
- **Web Scraping**: Real-time information gathering
- **Structured Responses**: JSON-formatted hotel search results

## Project Structure

```
staiz-api/
├── app/
│   ├── __init__.py
│   ├── core/                    # Core utilities and configurations
│   │   ├── __init__.py
│   │   ├── config.py           # Centralized configuration
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── middleware.py       # Custom middleware
│   │   └── security.py         # Security utilities
│   ├── chat/                   # AI Chat functionality
│   │   ├── __init__.py
│   │   ├── agent.py           # LangChain AI agent
│   │   ├── models.py          # Chat models and schemas
│   │   ├── response_models.py # Structured response models
│   │   ├── service.py         # Chat service layer
│   │   └── tools/             # AI tools (search, API, etc.)
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication models
│   │   ├── chat.py            # Chat and tab models
│   │   └── user.py            # User models
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── chat_repository.py # Chat data operations
│   │   └── user_repository.py # User data operations
│   ├── routers/                # API routers
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── chat.py            # Chat and tab endpoints
│   │   └── users.py           # User management endpoints
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   └── hybrid_memory_service.py # Memory management
│   ├── database.py             # MongoDB connection
│   ├── dependencies.py         # FastAPI dependencies
│   └── __init__.py
├── tests/                      # Test suite
├── main.py                     # FastAPI application
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Project configuration

├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Setup

### Prerequisites
- Python 3.8+ (for local development)
- MongoDB Atlas account (for production)
- Redis Cloud account (for production)
- OpenAI API key (optional, for AI features)

### Fly.io Deployment (Recommended)

The application is optimized for deployment on Fly.io with external database and cache services.

#### Quick Deploy to Fly.io

1. **Install Fly.io CLI:**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Authenticate and deploy:**
   ```bash
   fly auth login
   fly apps create staiz-api
   fly deploy
   ```

3. **Set environment variables:**
   ```bash
   fly secrets set MONGODB_URL="your-mongodb-atlas-url"
   fly secrets set REDIS_URL="your-redis-cloud-url"
   fly secrets set JWT_SECRET_KEY="your-secret-key"
   ```

4. **Access your app:**
   - API: https://staiz-api.fly.dev
   - API Docs: https://staiz-api.fly.dev/docs

#### External Services Setup

**MongoDB Atlas:**
1. Create free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Get connection string
3. Add to Fly.io secrets

**Redis Cloud:**
1. Create free database at [Redis Cloud](https://redis.com/try-free/)
2. Get connection details
3. Add to Fly.io secrets

📖 **For detailed Fly.io deployment instructions, see [FLY_DEPLOYMENT.md](FLY_DEPLOYMENT.md)**

### Local Development

For local development, you can use Docker:

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your external service URLs
   ```

2. **Start application:**
   ```bash
   docker-compose up -d
   ```

3. **Access locally:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Setup (Without Docker)
1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   # Create .env file with your configuration
   # See Configuration section below for required variables
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

The server will start at `http://localhost:8000`

## API Endpoints

### Authentication

#### POST `/auth/signup`
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "John Doe"
}
```

#### POST `/auth/login`
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### GET `/auth/me`
Get current user information (requires authentication).

### Chat Tabs Management

#### POST `/chat/tabs`
Create a new chat tab.

**Request Body:**
```json
{
  "title": "Hotel Search"
}
```

**Response:**
```json
{
  "tab_id": "uuid-string",
  "title": "Hotel Search",
  "session_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z",
  "last_activity": "2024-01-01T00:00:00Z",
  "message_count": 0,
  "is_active": true,
  "is_pinned": false,
  "order_index": 0
}
```

#### GET `/chat/tabs`
Get all chat tabs for the authenticated user.

#### PUT `/chat/tabs/{tab_id}`
Update a chat tab (title, pinned status, order).

**Request Body:**
```json
{
  "title": "Updated Title",
  "is_pinned": true,
  "order_index": 1
}
```

#### DELETE `/chat/tabs/{tab_id}`
Delete a chat tab and its conversation history.

### AI Chat

#### POST `/chat/message`
Send a message to the AI chat assistant.

**Request Body:**
```json
{
  "message": "I need hotel recommendations for Sydney",
  "tab_id": "uuid-string"
}
```

**Response (Regular Chat):**
```json
{
  "message": "I'd be happy to help you find hotel recommendations!",
  "session_id": "uuid-string",
  "tab_id": "uuid-string",
  "metadata": {
    "model": "gpt-4o",
    "history_length": 2
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response (Hotel Search):**
```json
{
  "message": "Here are some great hotel options for Sydney!",
  "hotelSearch": {
    "resultsTitle": "Hotels in Sydney CBD",
    "results": [
      {
        "id": "hotel_id",
        "name": "Medusa Hotel",
        "rating": 4.6,
        "reviews": 175,
        "stars": 5,
        "price": "$159",
        "priceLabel": "Best Price",
        "features": ["Free Wi-Fi", "Parking ($)", "Air conditioning"],
        "source": "Google Hotels",
        "sourceUrl": "http://www.medusa.com.au/",
        "imageUrl": "https://example.com/image.jpg",
        "aiNote": "Excellent rating, 5-star luxury, Free WiFi",
        "position": {
          "lat": -33.877673,
          "lng": 151.220436
        }
      }
    ]
  },
  "session_id": "uuid-string",
  "tab_id": "uuid-string",
  "metadata": {
    "model": "gpt-4o",
    "history_length": 3
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Conversation History

#### GET `/chat/history/{session_id}`
Get conversation history for a specific session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "I need hotel recommendations for Sydney",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Here are some great hotel options for Sydney!",
      "hotelSearch": {
        "resultsTitle": "Hotels in Sydney CBD",
        "results": [...]
      },
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "message_count": 2
}
```

#### DELETE `/chat/history/{session_id}`
Clear conversation history for a specific session.

### User Management

#### GET `/users/me`
Get current user information.

#### GET `/users/{user_id}`
Get user by ID (requires authentication).

#### GET `/users/`
Get all users with pagination (requires authentication).

### System Health

#### GET `/health`
Health check endpoint.

#### GET `/chat/health`
Chat system health check.

## Configuration

Create a `.env` file in the project root and configure:

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=staiz_db

# Redis
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI (optional)
OPENAI_API_KEY=your-openai-api-key

# SerpAPI (for hotel search)
SERPAPI_API_KEY=your-serpapi-key

# Pinecone (for vector search)
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## Chat Tabs Usage

### Creating a New Chat
1. User clicks "New Chat" button
2. Frontend calls `POST /chat/tabs` with title
3. Backend creates new tab and session
4. Frontend switches to the new tab
5. User can start typing messages

### Switching Between Tabs
1. User clicks on an existing tab
2. Frontend loads the tab's session_id
3. Frontend calls `GET /chat/history/{session_id}` to load messages
4. User can continue the conversation

### Sending Messages
1. User types message in current tab
2. Frontend sends `POST /chat/message` with tab_id
3. Backend processes message in the tab's session
4. Response includes tab_id for confirmation

### Managing Tabs
- **Rename**: Call `PUT /chat/tabs/{tab_id}` with new title
- **Pin**: Call `PUT /chat/tabs/{tab_id}` with `is_pinned: true`
- **Delete**: Call `DELETE /chat/tabs/{tab_id}`

## AI Features

### Hotel Search Capabilities
- **Location-based search**: City, neighborhood, landmark proximity
- **Date and guest filtering**: Check-in/out dates, number of guests
- **Amenity filtering**: WiFi, parking, pool, spa, etc.
- **Price range filtering**: Budget constraints
- **Star rating filtering**: 1-5 star hotels
- **Cancellation policy**: Free cancellation options
- **Special offers**: Deals and promotions

### AI Tools Available
- **mongodb_retrieve**: Database search for hotel information
- **api_call**: External API integration
- **web_scraper**: Real-time information gathering
- **pinecone_retrieve**: Vector search for similar content

### Memory System
- **Hybrid Approach**: Redis for speed, MongoDB for persistence
- **Conversation Context**: Maintains conversation history
- **Session Management**: Isolated conversations per tab
- **Structured Storage**: Full hotel search results preserved

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
pip install -r requirements-dev.txt
pytest
pytest --cov=app
```

### Code Quality
```bash
black .
flake8 .
mypy .
```

## Production Considerations

### Security
- Change JWT secret key in production
- Configure proper CORS origins
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting

### Database
- Configure MongoDB authentication
- Set up proper connection pooling
- Implement database backup strategies
- Monitor MongoDB performance

### Redis
- Configure Redis authentication
- Adjust connection pool size based on load
- Monitor Redis memory usage
- Use Redis clustering for high availability

### AI Services
- Monitor OpenAI API usage and costs
- Implement fallback models
- Cache AI responses where appropriate
- Monitor SerpAPI and Pinecone usage

### Monitoring & Logging
- Set up proper logging
- Implement error monitoring (e.g., Sentry)
- Add health checks and metrics
- Monitor API response times

## Testing the API

### Interactive Documentation
Visit `http://localhost:8000/docs` for Swagger UI documentation.

### Quick Test Commands

**Create a new tab:**
```bash
curl -X POST "http://localhost:8000/chat/tabs" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Hotel Search"}'
```

**Send a message:**
```bash
curl -X POST "http://localhost:8000/chat/message" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"message": "I need hotels in Sydney", "tab_id": "<tab_id>"}'
```

**Get conversation history:**
```bash
curl -X GET "http://localhost:8000/chat/history/<session_id>" \
     -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Common Issues

1. **Redis Connection Issues**
   - Check Redis server status: `redis-cli ping`
   - Increase `REDIS_MAX_CONNECTIONS` in `.env`
   - Monitor Redis memory usage

2. **MongoDB Connection Issues**
   - Verify MongoDB is running
   - Check connection string in `.env`
   - Ensure database permissions

3. **AI Service Issues**
   - Verify API keys are set correctly
   - Check API rate limits
   - Monitor API usage and costs

### Health Checks
```bash
# Overall health
curl http://localhost:8000/health

# Chat system health
curl http://localhost:8000/chat/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
