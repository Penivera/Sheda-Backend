from core.configs import pwd_context
from typing import Any
import os,shutil,aiofiles
from core.configs import Media_dir
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession



def hash_password(password:Any)->str:
    return pwd_context.hash(password)


def verify_password(password:Any,password_hash:str)->bool:
    return pwd_context.verify(password,password_hash)




async def upload_image(file:UploadFile,user,db:AsyncSession)->str:
    file_path = os.path.join(Media_dir, user.email)   
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await file.read(1024):  # Read in chunks of 1KB
            await buffer.write(chunk)
    user.profile_pic = file_path
    user.profile_pic = file_path
    #db.add(user) 
    await db.commit() 
    await db.refresh(user)
    
    return file_path
# Compare this snippet from Backend/app/utils/email.py:
    