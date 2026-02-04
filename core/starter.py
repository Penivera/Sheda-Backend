from contextlib import asynccontextmanager
from core.database import Base, engine
from fastapi import FastAPI, Depends, Form
from core.logger import logger
from core.configs import settings, redis

from app.utils.tasks import start_scheduler
from core.admin.seed import seed_superadmin
import cloudinary
from app.models.user import Admin
import os

# Alembic Imports
import subprocess
import sys

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database migrations using subprocess to avoid async/loop conflicts
    try:
        logger.info("Running database migrations...")
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        logger.info("Database migrations completed.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise e

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Tables Created")
    await seed_superadmin()
    start_scheduler()
    # Configuration
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    yield
