from fastapi import APIRouter, UploadFile, File, status
from app.services.user_service import ActiveUser, AdminUser

from core.dependecies import FileUploadException
from core.logger import logger
from app.schemas.user_schema import FileShow, FileDir
from typing import List
from app.utils.utils import read_media_dir
from cloudinary import uploader
from cloudinary.utils import cloudinary_url


router = APIRouter(
    tags=["Media"],
    prefix="/media",
)


# NOTE - Upload Profile Picture
@router.post(
    "/file-upload/{type}",
    response_model=FileShow,
    description="Add max size 500kb - 2MB",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_file(
    type: FileDir, current_user: ActiveUser, file: UploadFile = File(...)
):
    if not file.filename:
        raise FileUploadException
    try:
        file_content = await file.read()
        upload_result = uploader.upload(
            file_content,
            public_id=f"{type}/{current_user.id}/{file.filename}",
            overwrite=True,
            folder=type,
        )
        return FileShow(file_url=upload_result.get("secure_url"))  # type: ignore
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise FileUploadException from e  # type: ignore


# NOTE - Get the uploaded files
@router.get(
    "/file-upload/{type}",
    response_model=List[FileShow],
    description="Get uploaded files",
    status_code=status.HTTP_200_OK,
)
async def get_file(type: FileDir, current_user: AdminUser):
    file_list = await read_media_dir()
    file_list = [FileShow(file_url=file) for file in file_list]  # type: ignore
    return file_list
