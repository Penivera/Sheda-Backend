from fastapi import APIRouter, UploadFile, File, status, HTTPException
from app.services.user_service import ActiveUser, AdminUser
import os

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


# NOTE - IPFS Upload
@router.post(
    "/ipfs-upload",
    description="Upload file to IPFS (via Pinata or similar service)",
    status_code=status.HTTP_200_OK,
)
async def upload_to_ipfs(
    current_user: ActiveUser,
    file: UploadFile = File(...),
):
    """
    Uploads a file to IPFS.
    Currently configured to use Pinata if credentials are present, 
    otherwise returns a simulated hash for demonstration.
    """
    if not file.filename:
        raise FileUploadException

    content = await file.read()
    
    # Check for Pinata credentials in settings
    # For now, we'll try to use Pinata if keys exist, otherwise mock or error
    from core.configs import settings
    import httpx

    url = settings.PINATA_URL
    headers = {
        "pinata_api_key": settings.PINATA_API_KEY,
        "pinata_secret_api_key": settings.PINATA_SECRET_API_KEY,
    }
    files = {'file': (file.filename, content)}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, files=files, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        ipfs_hash = data.get("IpfsHash")
        return {"ipfs_url": f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}", "ipfs_hash": ipfs_hash}
    else:
        logger.error(f"Pinata IPFS upload failed: {response.text}")
        raise HTTPException(status_code=500, detail="IPFS upload failed")

    
