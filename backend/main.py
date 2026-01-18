from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from app.database import engine, Base, SessionLocal
from app.api import router
from app.exceptions import (
    DesensitizationError,
    FileUploadError,
    DocumentParsingError,
    RecognitionError,
    DesensitizationProcessingError,
    ExportError
)
from app.logging_config import configure_logging, get_logger
from app.init_rules import init_preconfigured_rules

# Configure structured logging
configure_logging(log_level="INFO", json_logs=True)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting application")
    Base.metadata.create_all(bind=engine)
    
    # Initialize pre-configured desensitization rules
    db = SessionLocal()
    try:
        init_preconfigured_rules(db)
    except Exception as e:
        logger.error(f"Failed to initialize pre-configured rules: {e}")
        db.rollback()
    finally:
        db.close()
    
    yield
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title="文档脱敏平台",
    description="Document Desensitization Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api/v1")


# Global exception handlers
@app.exception_handler(DesensitizationError)
async def desensitization_error_handler(request: Request, exc: DesensitizationError):
    """
    Handle all custom desensitization errors with structured response.
    
    Returns a JSON response with error code, message, and details.
    """
    logger.error(
        "desensitization_error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    
    # Determine HTTP status code based on error type
    status_code = status.HTTP_400_BAD_REQUEST
    
    if isinstance(exc, FileUploadError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, DocumentParsingError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, RecognitionError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, DesensitizationProcessingError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, ExportError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with generic error response.
    
    Logs the full exception details and returns a generic error message
    to avoid exposing internal implementation details.
    """
    logger.exception(
        "unexpected_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
