from fastapi import FastAPI
from app.routers import auth, listing, user, chat, media
from core.starter import lifespan
from core.configs import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    lifespan=lifespan,
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


# STUB - Set in full production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG_MODE else settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"] if settings.DEBUG_MODE else settings.METHODS,
    allow_headers=["*"] if settings.DEBUG_MODE else settings.ALLOW_HEADERS,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
