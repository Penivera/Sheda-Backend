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
        token_data = TokenData(scopes=token_scopes,username=identifier)
    except InvalidTokenError:
        raise InvalidCredentialsException
    token_scopes = payload.get("scopes", [])
    async with AsyncSessionLocal() as db:
        user = await get_user(db,token_data.username)
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

GetCurrentActUSer = Annotated[UserShow,Depends(get_current_active_user)]

async def get_current_active_seller(current_user:Annotated[UserShow, Security(get_current_user, scopes=["seller"])]):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Inactive User')
    return current_user

GetCurrentActSeller = Annotated[UserShow,Depends(get_current_active_seller)]



async def reset_password(user:UserInDB,db:DBSession,new_password:str):
    user.password = new_password
    db.add(user) 
    await db.commit()
    await db.refresh(user)
    


