from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth, listing, user, chat, media, websocket
from core.starter import lifespan
from core.configs import settings
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.error import ErrorHandlerMiddleware
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

# Ensure FastAdmin model registrations are imported BEFORE creating the admin app.
# `fastadmin.fastapi_app` is created at import-time and snapshots the registry.
from core.admin import fastadmin as _fastadmin_models  # noqa: F401
from fastadmin import fastapi_app as admin_app


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,  # type: ignore
        title="Sheda Solutions Backend",
        version="0.1.0",
        docs_url="/",
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

    # NOTE - Include Routers
    app.include_router(auth.router, prefix=settings.API_V_STR)
    app.include_router(user.router, prefix=settings.API_V_STR)
    app.include_router(listing.router, prefix=settings.API_V_STR)
    app.include_router(chat.router, prefix=settings.API_V_STR)
    app.include_router(media.router, prefix=settings.API_V_STR)

    # # STUB - Set in full production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG_MODE else settings.ORIGINS,
        allow_credentials=True,
        allow_methods=["*"] if settings.DEBUG_MODE else settings.METHODS,
        allow_headers=["*"] if settings.DEBUG_MODE else settings.ALLOW_HEADERS,
    )
    app.add_middleware(ErrorHandlerMiddleware)

    # Mount static files directory
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.mount(settings.ADMIN_ROUTE, admin_app)

    return app


app = create_app()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
