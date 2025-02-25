from fastapi import FastAPI
from core.starter import lifespan
from core.configs import origins
from app.routers import auth_router,user_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan,title='Sheda Solutions Backend',version='0.1.0',docs_url='/',description='Backend for Sheda Solutions')

#NOTE - Include Routers
app.include_router(auth_router.router)
app.include_router(user_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



