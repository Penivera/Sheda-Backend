from fastapi import FastAPI
from core.starter import lifespan
from app.routers.auth import auth_router
from core.dependecies import DBSession
app = FastAPI(lifespan=lifespan,title='Sheda Solutions Backend',version='0.1.0',docs_url='/',description='Backend for Sheda Solutions')

#NOTE - Include Routers
app.include_router(auth_router.router)





