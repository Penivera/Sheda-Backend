from contextlib import asynccontextmanager
from core.database import Base,engine
from fastapi import FastAPI
from core.configs import DEBUG_MODE,logger
from app import models



@asynccontextmanager
async def lifespan(app:FastAPI):
    async with engine.begin() as conn:
        '''if DEBUG_MODE:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info('Tables Dropped')'''
        
        await conn.run_sync(Base.metadata.create_all)
        logger.info('Tables Created')
        
    yield