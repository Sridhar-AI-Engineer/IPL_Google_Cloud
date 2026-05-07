import time
from pathlib import Path

from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest

from . import crud, database, models, schemas
from .config import settings
from .auth import create_access_token, create_refresh_token, TokenResponse
from .middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from .logging_config import logger, metrics
from .sentry_config import init_sentry
from .routers import user, match, decision, ml, analytics, admin, export
from .firebase_auth import get_firebase_status

# Initialize Sentry for error tracking
init_sentry()

# Create FastAPI app
app = FastAPI(
    title="IPL Agentic AI Coaching Simulator - Production",
    description="Real-time tactical IPL gameplay with AI coaching",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# ==================== MIDDLEWARE ====================
# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ==================== PROMETHEUS METRICS ====================
# Define metrics
REQUEST_COUNT = Counter(
    "ipl_requests_total",
    "Total requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "ipl_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"]
)
DECISIONS_SUBMITTED = Counter(
    "ipl_decisions_submitted_total",
    "Total decisions submitted"
)
USERS_CREATED = Counter(
    "ipl_users_created_total",
    "Total users created"
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for all requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    metrics.record_request(
        request.url.path,
        response.status_code,
        duration * 1000
    )
    
    logger.info(
        f"{request.method} {request.url.path} {response.status_code} {duration*1000:.2f}ms"
    )
    
    return response


# ==================== ROUTERS ====================
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(match.router, prefix="/matches", tags=["Matches"])
app.include_router(decision.router, prefix="/decisions", tags=["Decisions"])
app.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
app.include_router(analytics.router)
app.include_router(admin.router, tags=["Admin"])
app.include_router(export.router, tags=["Export"])


# ==================== STARTUP & SHUTDOWN ====================
@app.on_event("startup")
def startup_event():
    """Initialize database and seed data."""
    logger.info("Starting up application...")
    
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        crud.ensure_default_match(db)
        crud.seed_historical_decisions(db)
        crud.ensure_user(
            db,
            user=schemas.UserEnsure(username="Sridhar", email="sridhar@example.com")
        )
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        db.close()


@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application...")


# ==================== STATIC FILES ====================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


# ==================== PUBLIC ENDPOINTS ====================
@app.get("/", tags=["Public"])
def read_root():
    """Serve index page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to IPL Agentic AI Coaching Simulator!"}


@app.get("/dashboard", tags=["Public"])
def dashboard():
    """Serve dashboard page."""
    dashboard_file = FRONTEND_DIR / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    return {"message": "Dashboard file not found"}


# ==================== AUTHENTICATION ENDPOINTS ====================
@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(username: str, password: str = None):
    """User login (simplified - use OAuth2 in production)."""
    db = database.SessionLocal()
    try:
        user = crud.get_user_by_username(db, username)
        
        if not user:
            user = crud.create_user(
                db,
                user=schemas.UserCreate(username=username, email=None)
            )
        
        access_token = create_access_token(
            subject=str(user.id),
            is_admin=False
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        
        logger.info(f"User login: {username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_hours * 3600,
        )
    finally:
        db.close()


@app.post("/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
def refresh_token(refresh_token: str):
    """Refresh access token."""
    from .auth import verify_token
    
    payload = verify_token(refresh_token)
    
    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    new_access_token = create_access_token(subject=payload.sub)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiration_hours * 3600,
    )


@app.post("/auth/logout", tags=["Authentication"])
def logout(authorization: str = Header(None)):
    """User logout (token invalidation handled client-side)."""
    logger.info("User logout")
    return {"message": "Logged out successfully"}


# ==================== HEALTH & STATUS ====================
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint with detailed status."""
    return {
        "status": "healthy",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": settings.env,
        "firebase": get_firebase_status(),
        "database": "connected",
        "cache": "redis" if settings.redis_enabled else "memory",
        "sentry": settings.sentry_enabled,
    }


@app.get("/ready", tags=["Health"])
def readiness_check():
    """Kubernetes readiness probe."""
    try:
        db = database.SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"ready": True}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "error": str(e)}
        )


@app.get("/alive", tags=["Health"])
def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}


# ==================== MONITORING ====================
@app.get("/metrics", tags=["Monitoring"])
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return generate_latest()


@app.get("/stats", tags=["Monitoring"])
def stats_endpoint():
    """Application statistics."""
    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "metrics": metrics.get_metrics(),
        "stack": {
            "fastapi": True,
            "database": "postgresql" if "postgresql" in settings.database_url else "sqlite",
            "cache": "redis" if settings.redis_enabled else "memory",
            "sentry": settings.sentry_enabled,
            "rate_limiting": settings.rate_limit_enabled,
        }
    }


# ==================== TECH STACK ====================
@app.get("/stack", tags=["System"])
def stack_status():
    """Return availability status of all integrated tech stacks."""
    from ipl_agentic_coach.ai_agents.langchain_pipeline import langchain_pipeline
    from ipl_agentic_coach.ai_agents.langgraph_workflow import langgraph_workflow
    from ipl_agentic_coach.utils.analytics import PLOTLY_AVAILABLE
    from ipl_agentic_coach.utils.visualizations import is_available as mpl_ok

    return {
        "version": "2.0.0",
        "environment": settings.env,
        "backend": {
            "framework": "FastAPI",
            "python_version": "3.14",
        },
        "database": {
            "type": "postgresql" if "postgresql" in settings.database_url else "sqlite",
            "connected": True,
        },
        "cache": {
            "type": "redis" if settings.redis_enabled else "memory",
            "enabled": settings.redis_enabled,
        },
        "ai_ml": {
            "gemini": True,
            "langchain": langchain_pipeline.using_langchain,
            "langgraph": langgraph_workflow.using_langgraph,
            "ml_random_forest": True,
        },
        "analytics": {
            "plotly": PLOTLY_AVAILABLE,
            "matplotlib": mpl_ok(),
        },
        "monitoring": {
            "prometheus": settings.prometheus_enabled,
            "sentry": settings.sentry_enabled,
            "logging": settings.log_format,
        },
        "security": {
            "rate_limiting": settings.rate_limit_enabled,
            "firebase_auth": get_firebase_status()["firebase_auth_enabled"],
            "jwt_enabled": True,
        },
    }


@app.get("/langgraph/schema", tags=["AI"])
def langgraph_schema():
    """Return LangGraph workflow schema as JSON."""
    from ipl_agentic_coach.ai_agents.langgraph_workflow import langgraph_workflow
    return langgraph_workflow.get_schema()


@app.get("/langgraph/mermaid", tags=["AI"])
def langgraph_mermaid():
    """Return LangGraph workflow as Mermaid diagram text."""
    from ipl_agentic_coach.ai_agents.langgraph_workflow import langgraph_workflow
    return {"mermaid": langgraph_workflow.mermaid_diagram()}


@app.get("/leaderboard/top", tags=["Leaderboard"])
def leaderboard_top(limit: int = 10):
    """Get top users by points."""
    safe_limit = min(max(limit, 1), 50)
    db = database.SessionLocal()
    try:
        entries = crud.get_leaderboard(db, limit=safe_limit)
        return [
            {
                "id": entry.id,
                "username": entry.username,
                "points": entry.points,
            }
            for entry in entries
        ]
    finally:
        db.close()


# ==================== ERROR HANDLERS ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", extra={"path": request.url.path})
    
    if settings.sentry_enabled:
        from .sentry_config import capture_exception
        capture_exception(exc, context={"path": request.url.path})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )