from contextlib import asynccontextmanager
from core.database import Base,engine
from fastapi import FastAPI
from core.configs import DEBUG_MODE,logger
from app import models
from app.utils.tasks import start_scheduler



@asynccontextmanager
async def lifespan(app:FastAPI):
    async with engine.begin() as conn:
        '''if DEBUG_MODE:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info('Tables Dropped')'''
        start_scheduler()
        await conn.run_sync(Base.metadata.create_all)
        logger.info('Tables Created')
        
    yield