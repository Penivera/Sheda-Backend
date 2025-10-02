from contextlib import asynccontextmanager
from core.database import Base, engine
from fastapi import FastAPI
from core.logger import logger, settings
from app.utils.tasks import start_scheduler
import cloudinary


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables Created")
    start_scheduler()
    # Configuration
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    yield
