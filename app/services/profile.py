import os,aiofiles
from pathlib import Path
from core.configs import Media_dir
from fastapi import UploadFile,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import BaseUserSchema,UserUpdate,UserInDB,FileDir,RatingShow,AccountInfoBase
from app.models.user import Agent,BaseUser
from app.models.property import AccountInfo
from sqlalchemy.future import select
from sqlalchemy.engine import Result

async def upload_image(file:UploadFile,identifier,upload_dir:FileDir)->str:
    file_path = os.path.join(Media_dir,upload_dir,f'{identifier}{Path(file.filename).suffix}')   
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await file.read(1024):  #NOTE  Read in chunks of 1KB
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


async def updated_rating(agent_id:int,update_rating:int,db:AsyncSession):
    query = select(Agent).where(Agent.id==agent_id)
    result:Result = await db.execute(query)
    agent:Agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= 'User not found'
        )
    agent.rating+=update_rating
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return RatingShow(rating=agent.rating)

async def  create_new_payment_info(data:AccountInfoBase,db:AsyncSession,user:UserInDB):
    account_info = AccountInfo(
        **data,
        user_id = user.id,
    )
    db.add(account_info)
    await db.commit()
    await db.refresh(account_info)
    return account_info
    
async def get_account_info(db:AsyncSession,user_id:None):
    query = select(AccountInfo).where(AccountInfo.user_id==user_id)
    result:Result = db.execute(query)
    account_info = result.scalars().all()
    return account_info or []

async def update_account_info(update_data:AccountInfoBase,db:AsyncSession,current_user:UserInDB,account_info_id:int):
    account_info = next((account_info for account_info in current_user.account_info if account_info.id == account_info_id),None)
    if not account_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Account info not found or not owned by you'
        )
    for key,value in update_data.model_dump(exclude_unset=True):
        setattr(account_info,key,value)
        
    db.add(account_info)
    await db.commit()
    await db.refresh(account_info)
    return account_info

async def run_account_info_deletion(current_user:UserInDB,db:AsyncSession,account_info_id:int):
    account_info = next((account_info for account_info in current_user.account_info if account_info.id == account_info_id),None)
    if not account_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Account info not found or not owned by you'
        )
    db.delete(account_info)
    await db.commit()
    await db.refresh(account_info)
    return {'detail':'Account Info Deleted Succesfully'}