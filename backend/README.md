# ShareMeal Backend API

FastAPI backend for ShareMeal app with JWT authentication, MongoDB Atlas, and FCM push notifications.

## Quick Start

### Option 1: Run Locally (Recommended for Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your MongoDB URL and SECRET_KEY

# Run locally with hot reload
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --port 8000

# Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Option 2: Run with Docker Compose (Hot Reload Enabled)

```bash
# Start with docker-compose (auto-reloads on file changes)
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Note:** With docker-compose, code changes are automatically reflected - no rebuild needed!

### Option 3: Run with Docker (Production-like)

```bash
# Build image
docker build -t sharemeal-backend .

# Run container
docker run -p 8000:8000 --env-file .env sharemeal-backend
```

## Testing

1. **Register a new user:**
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password123", "name": "Test User"}'
   ```

2. **Login:**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password123"}'
   ```

3. **Use the access token:**
   ```bash
   curl -X GET http://localhost:8000/user \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

4. **Or use Swagger UI at `/docs`** - Click "Authorize" and paste your token

## API Endpoints

### Authentication (Public)

- `POST /auth/register` - Register a new user
  - Body: `{"email": "user@example.com", "password": "password123", "name": "User Name"}`
  - Returns: Access token and user info
  
- `POST /auth/login` - Login with email and password
  - Body: `{"email": "user@example.com", "password": "password123"}`
  - Returns: Access token and user info

### Food Items

All endpoints below require `Authorization: Bearer <jwt_access_token>` header.

- `GET /food` - List food items (with search filters)
- `POST /food` - Create food item
- `PATCH /food/{food_id}` - Update food item
- `DELETE /food/{food_id}` - Delete food item

### Requests

- `GET /requests` - Get user's requests
- `POST /food/{food_id}/request` - Create request
- `PATCH /requests/{request_id}` - Update request status
- `DELETE /requests/{request_id}` - Delete request

### User

- `GET /user` - Get user profile
- `POST /user/fcm-token` - Update FCM token

### Health

- `GET /health` - Health check endpoint

## Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Cloud Run deployment guide

## Environment Variables

Required:
- `MONGODB_URL` - MongoDB Atlas connection string
- `SECRET_KEY` - Secret key for JWT token signing (use a strong random string in production)

Optional:
- `PORT` - Server port (default: 8000, Cloud Run uses 8080)
- `FIREBASE_CREDENTIALS_PATH` - Path to Firebase service account JSON (for FCM in local dev)
  - On Cloud Run, FCM uses Workload Identity Federation automatically

See `.env.example` for template.

## MongoDB Collections

- `food_items` - Food listings
- `requests` - Food requests
- `users` - User profiles with FCM tokens

