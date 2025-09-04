# FastAPI Multi-Mode Authentication App

A flexible FastAPI application that supports two distinct operational modes with different authentication strategies and feature sets.

## 🏗️ Architecture Overview

This application implements a **Configuration-Driven Mode Architecture** that allows switching between:

- **Single User Mode (SU)**: Personal use with optional GitHub integration
- **Multi User Mode (MU)**: Enterprise-grade multi-tenant application

## 🚀 Features

### Core Features (Both Modes)
- ✅ FastAPI with automatic OpenAPI documentation
- ✅ GitHub API integration for repository management
- ✅ JWT-based authentication with secure token handling
- ✅ SQLAlchemy ORM with database migrations
- ✅ Comprehensive error handling and logging
- ✅ CORS configuration (restrictive in MU, permissive in SU)

### Single User Mode Features
- ✅ **No Auth**: Direct access without authentication
- ✅ **Optional GitHub Token**: Use personal GitHub token for API operations
- ✅ **Optional GitHub OAuth**: Lock app to specific GitHub user
- ✅ Full repository management capabilities
- ✅ File operations (create, read, update, delete)

### Multi User Mode Features
- ✅ **Mandatory GitHub OAuth**: All users must authenticate
- ✅ **User Management**: Admin panel for user administration
- ✅ **Role-Based Access Control**: Admin and regular user roles
- ✅ **User Statistics**: Analytics and reporting
- ✅ **Account Management**: Activate/deactivate users

## 📁 Project Structure

```
app/
├── core/
│   ├── config.py              # Environment-based configuration
│   ├── database.py            # Database connection and session management
│   ├── security.py            # JWT, encryption, password hashing
│   └── auth/
│       ├── strategies/        # Authentication strategy implementations
│       │   ├── base.py        # Abstract base strategy
│       │   ├── no_auth.py     # No authentication (SU mode)
│       │   ├── github_su.py   # GitHub OAuth for single user
│       │   └── github_mu.py   # GitHub OAuth for multi user
│       └── dependencies.py    # FastAPI dependencies for auth
├── models/
│   ├── user.py               # User database and Pydantic models
│   └── github.py             # GitHub API response models
├── services/
│   └── github_service.py     # GitHub API integration service
├── api/v1/
│   ├── auth.py               # Authentication endpoints
│   ├── github.py             # GitHub operations endpoints
│   └── users.py              # User management (MU mode only)
└── main.py                   # FastAPI application setup
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application Mode
APP_MODE=single_user  # or multi_user

# Database
DATABASE_URL=sqlite:///./app.db

# GitHub OAuth (required for auth modes)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Single User Mode Settings
ENABLE_SU_AUTH=false
SU_GITHUB_USERNAME=your_username
DEFAULT_GITHUB_TOKEN=ghp_your_token

# Multi User Mode Settings
MU_ADMIN_GITHUB_USERNAME=admin_username

# Security
SECRET_KEY=your-secret-key-change-this
```

### Configuration Modes

#### 1. Single User - No Auth
```bash
APP_MODE=single_user
ENABLE_SU_AUTH=false
DEFAULT_GITHUB_TOKEN=ghp_your_token  # Optional
```

#### 2. Single User - GitHub Auth
```bash
APP_MODE=single_user
ENABLE_SU_AUTH=true
SU_GITHUB_USERNAME=your_username
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

#### 3. Multi User Mode
```bash
APP_MODE=multi_user
MU_ADMIN_GITHUB_USERNAME=admin_username
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run the Application

```bash
# Development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
python app/main.py
```

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Configuration**: http://localhost:8000/config

## 🔐 Authentication Flows

### Single User Mode (No Auth)
```
User → App → GitHub API (with default token or X-GitHub-Token header)
```

### Single User Mode (GitHub Auth)
```
User → GitHub OAuth → App → Verify user is allowed → JWT Token → GitHub API
```

### Multi User Mode
```
User → GitHub OAuth → App → Create/Update user → JWT Token → Role-based access
```

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)
- `GET /auth/status` - Get authentication status
- `GET /auth/login` - Get login URL
- `GET /auth/github/callback` - GitHub OAuth callback
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info

### GitHub Integration (`/api/v1/github`)
- `GET /github/user` - Get GitHub user info
- `GET /github/repos` - List repositories
- `POST /github/repos` - Create repository
- `GET /github/repos/{owner}/{repo}` - Get repository details
- `GET /github/repos/{owner}/{repo}/contents` - Browse repository
- `PUT /github/repos/{owner}/{repo}/contents/{path}` - Create/update files

### User Management (`/api/v1/users`) - MU Mode Only
- `GET /users/` - List all users (admin)
- `GET /users/me` - Get current user
- `PUT /users/{id}` - Update user
- `POST /users/{id}/deactivate` - Deactivate user (admin)
- `POST /users/{id}/make-admin` - Grant admin privileges (admin)

## 🔒 Security Features

### Token Security
- ✅ GitHub tokens encrypted at rest using Fernet
- ✅ JWT tokens with expiration
- ✅ Secure cookie handling with HttpOnly flag
- ✅ CORS configuration based on mode

### Access Control
- ✅ Role-based permissions (admin/user)
- ✅ Mode-specific endpoint availability
- ✅ User activation/deactivation
- ✅ GitHub username validation in SU mode

### Data Protection
- ✅ No sensitive data in logs
- ✅ Encrypted token storage
- ✅ Secure session management
- ✅ Input validation and sanitization

## 🧪 Testing

### Manual Testing

1. **Test SU Mode (No Auth)**:
   ```bash
   curl http://localhost:8000/api/v1/github/repos
   ```

2. **Test Authentication**:
   ```bash
   curl http://localhost:8000/api/v1/auth/status
   ```

3. **Test GitHub Integration**:
   ```bash
   curl -H "X-GitHub-Token: ghp_your_token" \
        http://localhost:8000/api/v1/github/user
   ```

### Mode Switching

Change `APP_MODE` in `.env` and restart the application to test different modes.

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY .env .

EXPOSE 8000
CMD ["python", "app/main.py"]
```

### Environment-Specific Configuration

- **Development**: Use SQLite database
- **Production**: Use PostgreSQL with proper connection pooling
- **Security**: Use strong secret keys and enable HTTPS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.