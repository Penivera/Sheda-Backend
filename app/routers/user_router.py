from fastapi import APIRouter,UploadFile,File,HTTPException
from app.services.user_service import GetCurrentActUSer
from app.utils.utils import upload_image
from core.dependecies import FileUploadException,DBSession

router = APIRouter(tags=['Profile'],prefix='/profile',)

#NOTE - Upload Profile Picture
@router.post('/upload-pfp')
async def upload_pfp(*,current_user:GetCurrentActUSer,file: UploadFile = File(...),db:DBSession):
    if not file.filename:
        raise FileUploadException
    file_url = await upload_image(file,current_user,db)
    return {'filename': file_url}