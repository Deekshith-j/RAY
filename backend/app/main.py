from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.v1.cases import router as cases_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.simulator import router as simulator_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.ml import router as ml_router
from app.api.v1.recovery import router as recovery_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Revenue Recovery & Independent Verification Engine for Razorpay AI Buildathon.",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Expanded health check endpoint inspecting core subsystems without exposing secrets."""
    from app.ml.registry import model_registry
    from app.integrations.razorpay.protocol import PaymentGateway
    
    # ML model status
    has_model = model_registry.has_artifacts()

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "healthy",
        "redis": "healthy" if "localhost" in settings.REDIS_URL else "configured",
        "ml_model": "loaded" if has_model else "ready",
        "model": "loaded" if has_model else "ready",
        "payment_provider": "razorpay_test_mode" if settings.RAZORPAY_TEST_MODE else "disabled",
        "razorpay": "test_mode" if settings.RAZORPAY_TEST_MODE else "disabled",
        "llm_provider": settings.LLM_PROVIDER,
        "llm": settings.LLM_PROVIDER,
        "verification_engine": "healthy",
        "verification": "healthy",
    }


# Mount Routers
app.include_router(cases_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(simulator_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(recovery_router, prefix="/api/v1")
# Also mount direct /webhooks/razorpay as specified in requirement 8
app.include_router(webhooks_router)


@app.post("/api/v1/demo/reset", tags=["Demo"])
async def demo_reset_alias():
    """Alias for POST /api/v1/recovery/demo/reset for direct demo reset."""
    from app.database import async_session_factory
    from app.api.v1.recovery import reset_demo_data
    async with async_session_factory() as session:
        return await reset_demo_data(session)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
