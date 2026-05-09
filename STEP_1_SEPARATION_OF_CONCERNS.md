# Step 1: Separation of Concerns

## Overview

This step refactors the monolithic application into separate, independently deployable services following the 12-factor app methodology. This is essential for Kubernetes deployment.

## Architecture Changes

### Before (Monolithic)
```
Single FastAPI Application
├── API Routes
├── UI Routes (HTML templates)
├── Static Files
└── SQLite Database (embedded)
```

### After (Separated Services)
```
┌─────────────────────────────────────────────────────────┐
│                   Docker Compose                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Frontend   │  │     API      │  │  Database    │   │
│  │   (Nginx)    │  │  (FastAPI)   │  │ (PostgreSQL) │   │
│  │   Port 80    │  │  Port 8000   │  │  Port 5432   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│        │                  │                  │            │
│        └──────────────────┼──────────────────┘            │
│                           │                               │
│                  reservation-network                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Changes Made

### 1. Configuration Module (`app/config.py`)
- **Purpose**: Centralize all configuration using environment variables
- **12-Factor Compliance**: Configuration is loaded from environment, not hardcoded
- **Features**:
  - Database URL configuration
  - API host/port settings
  - Environment detection (dev/staging/prod)
  - Security settings
  - Logging configuration

**Usage**:
```python
from app.config import settings

print(settings.DATABASE_URL)
print(settings.is_production)
```

### 2. Health Checks Module (`app/health.py`)
- **Purpose**: Provide Kubernetes-compatible health check endpoints
- **Kubernetes Probes**:
  - **Liveness Probe** (`/health/live`): Is the app running?
  - **Readiness Probe** (`/health/ready`): Is the app ready for traffic?
  - **Startup Probe** (`/health/startup`): Has the app finished initializing?

**Endpoints**:
```
GET /health/live    → Returns 200 if app is alive
GET /health/ready   → Returns 200 if app is ready (DB connected)
GET /health/startup → Returns 200 if app has started
GET /health         → Legacy endpoint for backward compatibility
```

### 3. Updated Main Application (`app/main.py`)
- Integrated configuration module
- Added health check endpoints
- Improved logging
- Added startup/shutdown hooks
- Better error handling

### 4. API Dockerfile (`Dockerfile.api`)
- **Multi-stage build**: Reduces final image size
- **Non-root user**: Runs as `appuser` (UID 1000) for security
- **Health checks**: Built-in Docker health check
- **Optimized**: Only runtime dependencies in final image

**Build**:
```bash
docker build -f Dockerfile.api -t reservation-api:latest .
```

### 5. Frontend Dockerfile (`Dockerfile.frontend`)
- **Nginx-based**: Lightweight web server
- **Static file serving**: Optimized for HTML/CSS/JS
- **API proxy**: Routes API calls to backend
- **Security**: Non-root user, security headers
- **Caching**: Configured for optimal performance

**Build**:
```bash
docker build -f Dockerfile.frontend -t reservation-frontend:latest .
```

### 6. Nginx Configuration (`nginx.conf`)
- **Reverse proxy**: Routes requests to API backend
- **Static file serving**: Serves HTML, CSS, JS, images
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **Compression**: Gzip enabled for text content
- **Caching**: Optimized cache headers for different content types
- **Health endpoint**: `/health` for Docker/Kubernetes checks

**Key Routes**:
```
/api/*              → Proxied to API backend
/static/*           → Static files (CSS, JS)
/Images/*           → Image files
/                   → HTML pages
```

### 7. Docker Compose (`docker-compose.yml`)
- **Three services**: Frontend, API, Database
- **Networking**: All services on `reservation-network`
- **Health checks**: Each service has health checks
- **Volumes**: Persistent data for database
- **Environment variables**: Configurable via `.env`

**Services**:
1. **postgres**: PostgreSQL database (port 5432)
2. **api**: FastAPI backend (port 8000)
3. **frontend**: Nginx frontend (port 80)

### 8. Environment Configuration (`.env.example`)
- Comprehensive configuration template
- Organized by sections
- Includes all necessary variables
- Production-ready structure

## Running the Application

### Development with Docker Compose

1. **Copy environment file**:
```bash
cp .env.example .env
```

2. **Build images**:
```bash
docker-compose build
```

3. **Start services**:
```bash
docker-compose up
```

4. **Access the application**:
- Frontend: http://localhost
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health/ready

5. **Stop services**:
```bash
docker-compose down
```

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ENVIRONMENT=development
export DEBUG=true

# Run API
uvicorn app.main:app --reload --port 8000

# In another terminal, serve frontend
# Option 1: Use Python's built-in server
python -m http.server 8080

# Option 2: Use Node.js http-server
npx http-server -p 8080
```

## 12-Factor App Compliance

This refactoring ensures compliance with the 12-factor app methodology:

| Factor | Implementation |
|--------|-----------------|
| **Codebase** | Single codebase, multiple deployments |
| **Dependencies** | Explicit in `requirements.txt` |
| **Config** | Environment variables in `.env` |
| **Backing Services** | Database as external service |
| **Build/Run** | Separated via Docker |
| **Processes** | Stateless API service |
| **Port Binding** | Self-contained HTTP service |
| **Concurrency** | Multiple processes via Docker |
| **Disposability** | Fast startup/shutdown |
| **Dev/Prod Parity** | Same Docker images everywhere |
| **Logs** | Stdout/stderr logging |
| **Admin Tasks** | Separate scripts/commands |

## Kubernetes Readiness

The application is now ready for Kubernetes deployment:

✅ **Containerized**: Docker images for all services
✅ **Health Checks**: Liveness, readiness, startup probes
✅ **Configuration**: Environment-based configuration
✅ **Stateless**: API is stateless and scalable
✅ **Logging**: Structured logging to stdout
✅ **Graceful Shutdown**: Proper shutdown handlers
✅ **Resource Limits**: Can be configured in Kubernetes

## Next Steps

1. **Local Testing**: Test with `docker-compose up`
2. **Kubernetes Manifests**: Create YAML files for K8s deployment
3. **Helm Charts**: Package for Kubernetes deployment
4. **CI/CD Integration**: Automate builds and deployments

## Troubleshooting

### API container won't start
```bash
# Check logs
docker-compose logs api

# Verify health
curl http://localhost:8000/health/ready
```

### Frontend can't reach API
```bash
# Check nginx logs
docker-compose logs frontend

# Verify API is running
curl http://localhost:8000/health
```

### Database connection issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U reservation_user -d reservation_db -c "SELECT 1"
```

## Files Changed

- ✅ `app/config.py` - New configuration module
- ✅ `app/health.py` - New health check module
- ✅ `app/main.py` - Updated with config and health checks
- ✅ `Dockerfile.api` - New API container
- ✅ `Dockerfile.frontend` - New frontend container
- ✅ `nginx.conf` - New Nginx configuration
- ✅ `docker-compose.yml` - Updated with separated services
- ✅ `.env.example` - Updated with comprehensive config

## Commits

1. `feat: add configuration module for 12-factor app compliance`
2. `feat: add health check and readiness probes for Kubernetes`
3. `refactor: update main.py to use config and health checks`
4. `feat: add Dockerfile for API backend with multi-stage build`
5. `feat: add Dockerfile and nginx config for frontend`
6. `refactor: update docker-compose with separated services`
7. `docs: update .env.example with comprehensive configuration options`
