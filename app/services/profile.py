import os,aiofiles
from pathlib import Path
from core.configs import Media_dir
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import BaseUserSchema,UserUpdate,UserInDB,FileDir

async def upload_image(file:UploadFile,identifier,upload_dir:FileDir)->str:
    file_path = os.path.join(Media_dir,upload_dir,f'{identifier}{Path(file.filename).suffix}')   
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await file.read(1024):  # Read in chunks of 1KB
            await buffer.write(chunk)
    return file_path

async def update_pfp(user:BaseUserSchema,db:AsyncSession,file_path:str):
    user.profile_pic = file_path
    db.add(user)
    await db.commit()
    await db.refresh(user)
    


async def update_user(update_data:UserUpdate,db:AsyncSession,user:UserInDB):
    for key,value in update_data.model_dump(exclude_unset=True).items():
        setattr(user,key,value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


