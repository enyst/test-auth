from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from app.core.config import settings, AppMode
from app.core.database import create_tables
from app.api.v1 import auth, github, users

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=f"Multi-mode FastAPI application running in {settings.app_mode} mode",
    version="1.0.0",
    debug=settings.debug
)

# CORS configuration - more restrictive in MU mode
if settings.app_mode == AppMode.MULTI_USER:
    # Restrictive CORS for multi-user mode
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Specific origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
else:
    # More permissive CORS for single-user mode
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""

    # Create database tables
    create_tables()

    print(f"🚀 Starting FastAPI Multi-Mode App")
    print(f"📋 Mode: {settings.app_mode}")
    print(f"🔐 Authentication Required: {settings.requires_auth}")

    if settings.app_mode == AppMode.SINGLE_USER:
        if settings.enable_su_auth:
            print(f"👤 Single User Auth: {settings.su_github_username}")
        else:
            print("🔓 No authentication required")
            if settings.default_github_token:
                print("🔑 Default GitHub token configured")

    elif settings.app_mode == AppMode.MULTI_USER:
        print(f"👥 Multi User Mode")
        print(f"🛡️  Admin User: {settings.mu_admin_github_username}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "app_mode": settings.app_mode,
            "requires_auth": settings.requires_auth
        }
    )


@app.get("/")
async def root():
    """Root endpoint with app information"""

    return {
        "message": f"FastAPI Multi-Mode App running in {settings.app_mode} mode",
        "app_mode": settings.app_mode,
        "requires_auth": settings.requires_auth,
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "github": "/github",
            "users": "/users" if settings.app_mode == AppMode.MULTI_USER else None,
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""

    return {
        "status": "healthy",
        "app_mode": settings.app_mode,
        "database": "connected"  # Could add actual DB health check
    }


@app.get("/config")
async def get_config():
    """Get public configuration information"""

    config = {
        "app_mode": settings.app_mode,
        "requires_auth": settings.requires_auth,
        "github_oauth_configured": bool(settings.github_client_id),
        "features": {
            "github_integration": True,
            "user_management": settings.app_mode == AppMode.MULTI_USER,
            "admin_panel": settings.app_mode == AppMode.MULTI_USER
        }
    }

    # Add mode-specific config
    if settings.app_mode == AppMode.SINGLE_USER:
        config["single_user"] = {
            "auth_enabled": settings.enable_su_auth,
            "github_token_configured": bool(settings.default_github_token)
        }

    elif settings.app_mode == AppMode.MULTI_USER:
        config["multi_user"] = {
            "admin_configured": bool(settings.mu_admin_github_username)
        }

    return config


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1")

# Users router only in multi-user mode
if settings.app_mode == AppMode.MULTI_USER:
    app.include_router(users.router, prefix="/api/v1")


# Serve static files if directory exists
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
