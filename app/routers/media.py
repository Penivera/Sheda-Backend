from fastapi import APIRouter, UploadFile, File, status
from app.services.user_service import ActiveUser
from app.services.profile import upload_image
from core.dependecies import FileUploadException, DBSession
from app.schemas.user_schema import FileShow, FileDir
from typing import Annotated,List
from app.utils.utils import read_media_dir




router = APIRouter(tags=['Media'],prefix='/media',)

#NOTE - Upload Profile Picture
@router.post('/file-upload/{type}',response_model=FileShow,description='Add max size 500kb - 2MB',status_code=status.HTTP_202_ACCEPTED)
async def upload_file(type:FileDir,current_user:ActiveUser,file: UploadFile = File(...)):
    if not file.filename:
        raise FileUploadException
    file_url = await upload_image(file,current_user.id,type)
    return FileShow(file_url=file_url)

#NOTE - Get the uploaded files
@router.get('/file-upload/{type}',response_model=List[FileShow],description='Get uploaded files',status_code=status.HTTP_200_OK)
async def get_file(type:FileDir,current_user:ActiveUser):
    file_list = await read_media_dir()
    file_list = [FileShow(file_url=file) for file in file_list ] # type: ignore
    return file_list