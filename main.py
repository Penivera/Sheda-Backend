from fastapi import FastAPI
from app.routers import auth, listing, user
from core.starter import lifespan
from core.configs import origins,DEBUG_MODE
from app.routers import chat
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan,title='Sheda Solutions Backend',version='0.1.0',docs_url='/',description='Backend for Sheda Solutions',debug=DEBUG_MODE,servers=[
    {"url": "https://sheda-backend-production.up.railway.app", "description": "Production Server"},
    {"url": "http://localhost:8000", "description": "Local Development"},
    ]
              )

#NOTE - Include Routers
app.include_router(auth.router,prefix='/api')
app.include_router(user.router,prefix='/api')
app.include_router(listing.router,prefix='/api')
app.include_router(chat.router,prefix='/api')


#STUB - Set in full production
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



