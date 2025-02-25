from core.dependecies import TokenDependecy,InvalidCredentialsException
import jwt
from jwt.exceptions import InvalidTokenError
from core.configs import SECRET_KEY,ALGORITHM,redis,logger,BLACKLIST_PREFIX
from app.schemas.auth_schema import TokenData
from app.services.auth import get_user
from core.database import AsyncSessionLocal
from app.schemas.auth_schema import User
from fastapi import Depends,HTTPException,status
from typing import Annotated

async def get_current_user(token:TokenDependecy):
    is_blacklisted = await redis.get(BLACKLIST_PREFIX.format(token))
    logger.info(f'Blacklisted {is_blacklisted}')
    if is_blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Token has been revoked')
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        identifier = payload.get('sub')
        logger.info(f'Identifier {identifier}')
        if not identifier:
            raise InvalidCredentialsException
        token_data = TokenData(username=identifier)
    except InvalidTokenError:
        raise InvalidCredentialsException
    async with AsyncSessionLocal() as db:
        user = await get_user(db,token_data.username)
        logger.info(f'User {user.username} fetched')
    if not user:
        logger.error('User not found')
        raise InvalidCredentialsException
    return user
    
    
async def get_current_active_user(current_user:User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Inactive User')
    return current_user


GetCurrentActUSer = Annotated[User,Depends(get_current_active_user)]
GetUser = Annotated[str,Depends(get_current_user)]