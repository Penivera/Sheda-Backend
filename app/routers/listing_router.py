from fastapi import APIRouter,UploadFile,File,HTTPException,status
from app.services.profile import upload_image,update_pfp,update_user
from core.dependecies import FileUploadException,DBSession
from app.schemas.property_schema import PropertyBase,PropertyShow
from app.services.listing import create_property_listing
from app.services.user_service import GetCurrentActSeller


router = APIRouter(prefix='/property',tags=['Property'])

@router.post('/list-property',response_model=PropertyShow,description='Upload Property',status_code=status.HTTP_201_CREATED)
async def list_property(current_user:GetCurrentActSeller,payload:PropertyBase,db:DBSession):
    return await create_property_listing(current_user,payload,db)
    