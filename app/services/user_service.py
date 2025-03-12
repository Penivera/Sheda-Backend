from core.dependecies import TokenDependecy,InvalidCredentialsException,DBSession
import jwt
from jwt.exceptions import InvalidTokenError
from core.configs import SECRET_KEY,ALGORITHM,redis,logger,BLACKLIST_PREFIX
from app.schemas.auth_schema import TokenData
from app.services.auth import get_user
from core.database import AsyncSessionLocal
from app.schemas.user_schema import UserShow,UserInDB
from fastapi import Depends,HTTPException,status,Security
from typing import Annotated
from app.utils.enums import AccountTypeEnum
from fastapi.security import SecurityScopes
from pydantic import EmailStr
from app.utils.utils import blacklist_token,token_exp_time

async def get_current_user(security_scopes:SecurityScopes,token:TokenDependecy):
    is_blacklisted = await redis.get(BLACKLIST_PREFIX.format(token))
    logger.info(f'Blacklisted {bool(is_blacklisted)}')
    if is_blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Token has been revoked')
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = 'Bearer'
    try:
        payload:dict = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        identifier = payload.get('sub')
        logger.info(f'Identifier {identifier}')
        if not identifier:
            raise InvalidCredentialsException
    except InvalidTokenError:
        raise InvalidCredentialsException
    token_scopes = payload.get("scopes", [])
    token_data = TokenData(scopes=token_scopes,username=identifier)
    user = await get_user(token_data.username)
    logger.info(f'User {user.username} fetched')
    if not user:
        logger.error('User not found')
        raise InvalidCredentialsException
    #NOTE - Scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user
    
GetUser = Annotated[UserShow,Depends(get_current_user)]

async def get_current_active_user(current_user:GetUser):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Inactive User')
    return current_user

ActiveUser = Annotated[UserShow,Depends(get_current_active_user)]

async def get_current_active_agent(current_user:Annotated[UserShow, Security(get_current_user, scopes=["agent"])]):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Inactive User')
    return current_user

ActiveAgent = Annotated[UserShow,Depends(get_current_active_agent)]

async def get_verified_otp_email(security_scopes:SecurityScopes,token:TokenDependecy):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = 'Bearer'
    try:
        payload:dict = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email = payload.get('sub')
        logger.info(f'OTP Email {email}')
        if not email:
            raise InvalidCredentialsException
    except InvalidTokenError:
        raise InvalidCredentialsException
    token_scopes = payload.get("scopes", [])
    
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    token_exp = await token_exp_time(token)
    await blacklist_token(token,token_exp)
    return email
    
    

OtpVerification = Annotated[EmailStr, Security(get_verified_otp_email, scopes=["otp"])]

async def reset_password(user:UserInDB,db:DBSession,new_password:str):
    user.password = new_password
    db.add(user) 
    await db.commit()
    await db.refresh(user)
    return True
    


