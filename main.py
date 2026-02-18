import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import (
    auth,
    listing,
    user,
    chat,
    media,
    websocket,
    rating,
    transactions,
    notifications,
    wallets,
    minted_property,
    indexer,
)

try:
    from app.routers import notifications_enhanced, transactions_enhanced, health
except ImportError:
    notifications_enhanced = None
    transactions_enhanced = None
    health = None
from core.starter import lifespan
from core.configs import settings
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.error import ErrorHandlerMiddleware, setup_exception_handlers
from core.middleware.rate_limit import (
    limiter,
    RateLimitMiddleware,
    rate_limit_exceeded_handler,
)
from core.admin.admin import admin
from slowapi.errors import RateLimitExceeded
from core.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,  # type: ignore
        title="Sheda Solutions Backend",
        version="0.1.0",
        docs_url="/sheda-docs",
        description="Backend for Sheda Solutions",
        debug=settings.DEBUG_MODE,
        servers=(
            [
                {"url": settings.DEV_URL, "description": "Local Development"},
                {"url": settings.PROD_URL, "description": "Production Server"},
            ]
            if settings.DEBUG_MODE
            else [
                {"url": settings.PROD_URL, "description": "Production Server"},
                {"url": settings.DEV_URL, "description": "Local Development"},
            ]
        ),
    )

    if not os.path.exists("static"):
        os.makedirs("static")
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(settings.BASE_DIR, "static")),
        name="static",
    )

    # NOTE - Include Routers
    app.include_router(auth.router, prefix=settings.API_V_STR)
    app.include_router(user.router, prefix=settings.API_V_STR)
    app.include_router(listing.router, prefix=settings.API_V_STR)
    app.include_router(chat.router, prefix=settings.API_V_STR)
    app.include_router(media.router, prefix=settings.API_V_STR)
    app.include_router(websocket.router, prefix=settings.API_V_STR)
    app.include_router(rating.router, prefix=settings.API_V_STR)
    app.include_router(transactions.router, prefix=settings.API_V_STR)
    app.include_router(notifications.router, prefix=settings.API_V_STR)

    # Phase 2 Enhanced Routers
    if notifications_enhanced:
        app.include_router(notifications_enhanced.router, prefix=settings.API_V_STR)
    if transactions_enhanced:
        app.include_router(transactions_enhanced.router, prefix=settings.API_V_STR)

    # Phase 3 Health Checks
    if health:
        app.include_router(health.router, prefix=settings.API_V_STR)

    app.include_router(wallets.router, prefix=settings.API_V_STR)
    app.include_router(minted_property.router, prefix=settings.API_V_STR)
    app.include_router(indexer.router, prefix=settings.API_V_STR)

    # NOTE - Fully permissive CORS (dev only, restrict in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # NOTE - Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)

    # NOTE - Add error handling middleware
    app.add_middleware(ErrorHandlerMiddleware)

    # NOTE - Setup exception handlers for proper error responses
    setup_exception_handlers(app)

    # NOTE - Register rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # NOTE - Mount Starlette Admin
    admin.mount_to(app)

    logger.info("FastAPI application initialized successfully")

    return app


app = create_app()

# Health check endpoints are now in app/routers/health.py
