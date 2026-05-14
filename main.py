# main.py
from fastapi import FastAPI, Request ,HTTPException
from fastapi.responses import JSONResponse
import traceback
from fastapi.exceptions import RequestValidationError
from fastapi import status
from app.core.logging import get_logger
from app.database import engine, Base
from collections import defaultdict
import time
from fastapi.middleware.cors import CORSMiddleware
# Import models so SQLAlchemy registers them before create_all
from app.models import user, book, borrow  # noqa: F401

# Routers
from app.routers.auth import router as auth_router
from app.routers.usersprotected import router as users_router
from app.routers.books import router as books_router
from app.routers.admin import router as admin_router

logger = get_logger()

app = FastAPI(
    title="Library Management System",
    description="Backend API for Library with JWT Auth & Role System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # For development - allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create all tables
Base.metadata.create_all(bind=engine)


# ================= REGISTER ROUTERS =================
app.include_router(auth_router,  prefix="/auth",   tags=["Authentication"])
app.include_router(users_router, prefix="/users",  tags=["Users"])
app.include_router(books_router, prefix="/books",  tags=["Books"])
app.include_router(admin_router, prefix="/admin",  tags=["Admin"])
# ====================================================



# ================= GLOBAL ERROR HANDLER =================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected Error: {type(exc).__name__} - {str(exc)}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error_type": type(exc).__name__,
        }
    )


# =======================================================


# ================= MONITORING ENDPOINTS =================
request_counts = defaultdict(int)
error_counts = defaultdict(int)
response_times = []


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time


    request_counts[request.url.path] += 1
    if response.status_code >= 400:
        error_counts[request.url.path] += 1

    if len(response_times) > 100:
        response_times.pop(0)
    response_times.append(process_time * 1000)

    return response


@app.get("/monitoring/dashboard")
def monitoring_dashboard():

    total_requests = sum(request_counts.values())
    total_errors = sum(error_counts.values())
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    return {
        "status": "running",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system_health": {
            "status": "healthy",
            "redis": "connected",
            "database": "connected"
        },
        "api_metrics": {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": f"{(total_errors / total_requests * 100) if total_requests > 0 else 0:.2f}%",
            "average_response_time_ms": round(avg_response_time, 2)
        },
        "endpoints": dict(request_counts),
        "recent_errors": dict(error_counts),
        "message": "Monitoring Dashboard - Library Management System"
    }



@app.get("/monitoring/health")
def health_check():

    redis_status = "not_configured"

    try:
        from app.core.cache import redis_client
        if redis_client.ping():
            redis_status = "connected"
        else:
            redis_status = "disconnected"
    except Exception as e:
            redis_status = "not_configured"

    return {
        "status": "healthy",
        "service": "Library Management System",
        "version": "1.0.0",
        "redis": redis_status,
        "database": "connected"
    }


@app.get("/monitoring/info")
def system_info():

    return {
        "app_title": app.title,
        "version": app.version,
        "docs_url": "/docs",
        "status": "running"
    }


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "✅ Library Management System is running successfully!",
        "documentation": "/docs"
    }
