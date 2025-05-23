from core.configs import pwd_context,logger,redis,user_data_prefix,otp_prefix,BLACKLIST_PREFIX,logger,SECRET_KEY,ALGORITHM,Media_dir
import jwt
from typing import Any
from datetime import datetime,timezone
from pydantic import AnyUrl
import os

def decode_url(url:AnyUrl)->str:
    return str(url)

def hash_password(password:Any)->str:
    return pwd_context.hash(password)


def verify_password(password:Any,password_hash:str)->bool:
    return pwd_context.verify(password,password_hash)


async def verify_otp(otp:str,email:str):
    stored_otp = await redis.get(otp_prefix.format(email))
    if stored_otp and stored_otp.decode() == otp:
        logger.info(f'otp verified')
        await redis.delete(otp_prefix.format(email))
        logger.info(f'{email} OTP Data deleted from redis')
        return True
    logger.error('OTP not found')
    return False

async def blacklist_token(token:str,time:int):
    await redis.setex(BLACKLIST_PREFIX.format(token),time,'blacklisted')
    logger.info(f'Token added to blacklist for {time/60} minutes')
    
async def token_exp_time(token:str):
    payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
    exp_timestamp = payload.get("exp")
    logger.info(f'Exp timestamp {exp_timestamp}')
    if not exp_timestamp:
        return None
    current_time = datetime.now(timezone.utc).timestamp()
    remaining_time = max(0, int(exp_timestamp - current_time))
    return remaining_time

async def read_media_dir() -> list[str] | None:
    os.makedirs(Media_dir, exist_ok=True)
    logger.info(f'Media directory created at {Media_dir}')
    for root, dirs, files in os.walk(Media_dir):
        logger.info(f'Root directory: {root}')
        logger.info(f'Directories: {dirs}')
        logger.info(f'Files: {files}')
        for directory in dirs:
            file_list = [file for file in os.listdir(os.path.join(root,directory)) if os.path.isfile(os.path.join(root,directory, file))]
            logger.info(file_list)
        return file_list
        '''for file in files:
            file_path = os.path.join(root, file)
            logger.info(f'File found: {file_path}')
            if not os.path.isfile(file_path):
                logger.error(f'File not found: {file_path}')
                continue'''
           