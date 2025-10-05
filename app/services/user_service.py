from email.policy import HTTP
from core.dependecies import HTTPBearerDependency, InvalidCredentialsException, DBSession
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from core.configs import settings, redis
from core.logger import logger
from app.schemas.auth_schema import TokenData
from app.services.auth import get_user
from app.schemas.user_schema import UserShow, UserInDB
from fastapi import Depends, HTTPException, status, Security
from typing import Annotated
from app.utils.enums import AccountTypeEnum, UserRole
from fastapi.security import SecurityScopes
from pydantic import EmailStr
from app.utils.utils import blacklist_token, token_exp_time
from app.models.user import BaseUser
from dataclasses import dataclass
from typing import List

@dataclass
class UserContext:
    user: BaseUser
    scopes: List[str]
    
async def user_context(
    security_scopes: SecurityScopes, credentials: HTTPBearerDependency, db: DBSession
) -> UserContext:
    token = credentials.credentials
    is_blacklisted = await redis.get(settings.BLACKLIST_PREFIX.format(token))
    logger.info(f"Blacklisted: {bool(is_blacklisted)}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )  # type: ignore
        identifier = payload.get("sub")
        logger.info(f"Identifier {identifier}")
        if not identifier:
            raise InvalidCredentialsException
    except (InvalidTokenError, ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
    token_scopes = payload.get("scopes", [])


    token_data = TokenData(scopes=token_scopes, sub=identifier)
    account_type = token_data.scopes[0] if token_data.scopes in AccountTypeEnum.to_list() else AccountTypeEnum.client # type: ignore
    logger.info(f"Account type: {account_type}")
    user: UserInDB = await get_user(token_data.sub, db, account_type) # type: ignore
    if not user:
        logger.error(f"User not found")
        raise InvalidCredentialsException
    # NOTE - Scopes
    logger.info(f"User {user.username} fetched")
    if "admin" in token_scopes and user.role == UserRole.ADMIN:  # NOTE - Admin access
        return UserContext(user=user, scopes=token_scopes)
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:  # type: ignore # type: ignore # type: ignore
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return UserContext(user=user, scopes=token_scopes)

GetUserContext = Annotated[UserContext, Depends(user_context)]

async def get_current_user(get_user_context: GetUserContext):
        # NOTE ensure that OTP tokens are not used in this route
    if "otp" in get_user_context.scopes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP token not permitted in this route",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_user_context.user



GetUser = Annotated[UserShow, Depends(get_current_user)]


async def get_current_active_user(current_user: GetUser):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveUser = Annotated[UserInDB, Depends(get_current_active_user)]


async def get_current_active_agent(
    current_user: Annotated[UserShow, Security(get_current_user, scopes=["agent"])],
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveAgent = Annotated[UserInDB, Depends(get_current_active_agent)]


async def active_client(
    current_user: Annotated[UserShow, Security(get_current_user, scopes=["client"])],
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveClient = Annotated[UserInDB, Depends(active_client)]


async def get_verified_otp_email(user_context: GetUserContext,credentials: HTTPBearerDependency
):
    token = credentials.credentials

    token_exp = await token_exp_time(token)
    await blacklist_token(token, token_exp)  # type: ignore
    return user_context.user.email


OtpVerification = Annotated[EmailStr, Security(get_verified_otp_email, scopes=["otp"])]


async def require_admin_scope(
    current_user: Annotated[UserInDB, Security(get_current_user, scopes=["admin"])],
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    # Check user role
    if UserRole.ADMIN != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return current_user


AdminUser = Annotated[UserInDB, Depends(require_admin_scope)]


async def reset_password(user: UserInDB, db: DBSession, new_password: str):
    user.password = new_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
