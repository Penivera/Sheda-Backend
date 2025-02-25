import os,aiofiles
from pathlib import Path
from core.configs import Media_dir
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import BaseUserSchema



async def upload_image(file:UploadFile,user:BaseUserSchema,db:AsyncSession)->str:
    file_path = os.path.join(Media_dir, f'{user.email}{Path(file.filename).suffix}')   
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await file.read(1024):  # Read in chunks of 1KB
            await buffer.write(chunk)
    user.profile_pic = file_path
    user.profile_pic = file_path
    db.add(user) 
    await db.commit() 
    await db.refresh(user)
    
    return file_path