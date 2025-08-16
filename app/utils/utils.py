from core.configs import settings,logger,redis
import jwt
from typing import Any
from datetime import datetime,timezone
from pydantic import AnyUrl
import os

def decode_url(url:AnyUrl)->str:
    return str(url)

def hash_password(password:Any)->str:
    return settings.pwd_context.hash(password)


def verify_password(password:Any,password_hash:str)->bool:
    return settings.pwd_context.verify(password,password_hash)


async def verify_otp(otp:str,email:str):
    stored_otp = await redis.get(settings.OTP_PREFIX.format(email))
    if stored_otp and stored_otp.decode() == otp:
        logger.info(f'otp verified')
        await redis.delete(settings.OTP_PREFIX.format(email))
        logger.info(f'{email} OTP Data deleted from redis')
        return True
    logger.error('OTP not found')
    return False

async def blacklist_token(token:str,time:int):
    await redis.setex(settings.BLACKLIST_PREFIX.format(token),time,'blacklisted')
    logger.info(f'Token added to blacklist for {time/60} minutes')
    
async def token_exp_time(token:str):
    payload = jwt.decode(token,settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # type: ignore
    exp_timestamp = payload.get("exp")
    logger.info(f'Exp timestamp {exp_timestamp}')
    if not exp_timestamp:
        return None
    current_time = datetime.now(timezone.utc).timestamp()
    remaining_time = max(0, int(exp_timestamp - current_time))
    return remaining_time

async def read_media_dir() -> list[str] | None:
    logger.info(f'Media directory created at {settings.MEDIA_DIR}')
    for root, dirs, files in os.walk(settings.MEDIA_DIR):
        logger.info(f'Root directory: {root}')
        logger.info(f'Directories: {dirs}')
        logger.info(f'Files: {files}')
        for directory in dirs:
            file_list = [file for file in os.listdir(os.path.join(root,directory)) if os.path.isfile(os.path.join(root,directory, file))]
            logger.info(file_list)
        return file_list

           