from fastapi import APIRouter,UploadFile,File,HTTPException,status
from core.dependecies import FileUploadException,DBSession
from app.schemas.property_schema import PropertyBase,PropertyShow,PropertyListResponse
from app.services.listing import create_property_listing,get_user_properties
from app.services.user_service import GetCurrentActSeller
from typing import List


router = APIRouter(prefix='/property',tags=['Property'],)

@router.post('/list-property',response_model=PropertyShow,description='Upload Property',status_code=status.HTTP_201_CREATED)
async def list_property(current_user:GetCurrentActSeller,payload:PropertyBase,db:DBSession):
    return await create_property_listing(current_user,payload,db)

@router.get('/me',response_model=PropertyListResponse,status_code=status.HTTP_200_OK)
async def get_my_listing(current_user:GetCurrentActSeller,db:DBSession):
    return await get_user_properties(current_user,db)
    
    