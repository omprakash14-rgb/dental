import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.db.database import init_db
from app.ai.model_loader import get_dental_model
from app.api.endpoints import router as api_router
from app.api.auth_endpoints import router as auth_router
from app.core.config import settings
from app.core.auth import decode_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dentalai")

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
uploads_dir = settings.UPLOADS_DIR
os.makedirs(uploads_dir, exist_ok=True)

frontend_dist = os.path.join(project_root, "frontend", "dist")

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and Warm Up Pretrained AI Model
    logger.info("Initializing DentalAI Backend Service (%s mode)...", settings.ENVIRONMENT)
    try:
        init_db()
    except Exception as e:
        logger.error("Database initialization failed: %s", e)

    try:
        logger.info("Warming up pretrained ResNet-50 Dental Model...")
        get_dental_model()
        logger.info("AI Model warmed up and resident in memory.")
    except Exception as e:
        logger.error("Failed to preload dental AI model: %s", e)

    yield

    logger.info("Shutting down DentalAI Service.")

app = FastAPI(
    title="DentalAI – AI-Powered Dental Disease Detection API",
    description="Production-grade AI platform for analyzing multi-view intraoral photographs and detecting dental pathologies.",
    version=settings.VERSION,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# OWASP Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Protected patient uploads route
@app.get("/uploads/{filename}")
async def get_uploaded_image(filename: str, request: Request):
    """
    Access-controlled image endpoint:
    - Sample evaluation images (prefix 'sample_') are publicly readable for testing.
    - Clinical patient images require authenticated token in Authorization header or query parameter 'token'.
    - Validates against directory traversal attacks.
    """
    clean_filename = os.path.basename(filename)
    safe_path = os.path.abspath(os.path.join(uploads_dir, clean_filename))
    if not safe_path.startswith(os.path.abspath(uploads_dir)):
        raise HTTPException(status_code=403, detail="Invalid file path.")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Requested image not found.")

    # Allow sample images for demo and testing
    if clean_filename.startswith("sample_"):
        return FileResponse(safe_path)

    # For patient clinical images, verify authentication
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif "token" in request.query_params:
        token = request.query_params["token"]

    if not token and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access to clinical patient photographs requires authentication."
        )

    return FileResponse(safe_path)

# Include API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api")

# Mount built frontend if available
if os.path.exists(frontend_dist):
    logger.info("Mounting frontend production build from: %s", frontend_dist)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow /api and /uploads to pass through
        if full_path.startswith("api") or full_path.startswith("uploads") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"service": "DentalAI", "status": "online"}
else:
    @app.get("/")
    def read_root():
        return {
            "service": "DentalAI - Dental Disease Detection API",
            "status": "online",
            "docs_url": "/docs",
            "health_check": "/api/health"
        }
