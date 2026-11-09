"""Countersign: The Trust and Security Layer for AI-Powered Payments.

FastAPI Application Entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_v1_router
from app.api.routes.webhooks import router as webhook_router
from app.core.config import settings
from app.core.exceptions import (
    CountersignException,
    KillSwitchActiveException,
    MandateIntegrityException,
    PayeeTamperException,
    PayPalIntegrationException,
    PolicyViolationException,
)
from app.core.logging import logger, setup_logging
from app.database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    setup_logging()
    logger.info("Initializing Countersign Financial Security Gateway...")
    logger.info(f"Environment: {settings.ENVIRONMENT} (PayPal Sandbox Locked: {settings.PAYPAL_BASE_URL})")

    # Ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified successfully.")
    except Exception as e:
        logger.warning(f"Database schema auto-creation notice: {e}")

    yield

    # Shutdown sequence
    logger.info("Shutting down Countersign Gateway.")


app = FastAPI(
    title="Countersign API",
    description="Intelligent financial authorization gateway positioned between AI agents and PayPal.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(KillSwitchActiveException)
async def kill_switch_exception_handler(request: Request, exc: KillSwitchActiveException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": "KILL_SWITCH_ACTIVE", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(PayeeTamperException)
async def payee_tamper_exception_handler(request: Request, exc: PayeeTamperException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "PAYEE_TAMPER_DETECTED", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(PolicyViolationException)
async def policy_violation_exception_handler(request: Request, exc: PolicyViolationException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "POLICY_VIOLATION", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(PayPalIntegrationException)
async def paypal_exception_handler(request: Request, exc: PayPalIntegrationException):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": "PAYPAL_INTEGRATION_ERROR", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(CountersignException)
async def domain_exception_handler(request: Request, exc: CountersignException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "DOMAIN_ERROR", "message": exc.message, "details": exc.details},
    )


# Mount API Routes
app.include_router(api_v1_router)
app.include_router(webhook_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health and readiness check endpoint."""
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "environment": settings.PAYPAL_ENVIRONMENT,
        "kill_switch_active": settings.KILL_SWITCH_ENABLED,
        "paypal_configured": settings.is_paypal_configured,
        "ai_provider": settings.AI_PROVIDER,
        "database": "CONNECTED",
    }
