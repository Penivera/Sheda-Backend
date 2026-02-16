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
from core.starter import lifespan
from core.configs import settings
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.error import ErrorHandlerMiddleware
from core.admin.admin import admin


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
    app.include_router(wallets.router, prefix=settings.API_V_STR)
    app.include_router(minted_property.router, prefix=settings.API_V_STR)
    app.include_router(indexer.router, prefix=settings.API_V_STR)

    # NOTE - Fully permissive CORS (dev only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ErrorHandlerMiddleware)

    # Mount static files directory (create if not exists for production)

    admin.mount_to(app)

    return app


app = create_app()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
