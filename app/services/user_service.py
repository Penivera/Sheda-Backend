from email.policy import HTTP
from core.dependecies import (
    HTTPBearerDependency,
    InvalidCredentialsException,
    DBSession,
)
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


async def get_token_payload(credentials: HTTPBearerDependency) -> TokenData:
    token = credentials.credentials
    is_blacklisted = await redis.get(settings.BLACKLIST_PREFIX.format(token))
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )
    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )  # type: ignore
        identifier = payload.get("sub")
        if not identifier:
            raise InvalidCredentialsException
        token_scopes = payload.get("scopes", [])
        return TokenData(scopes=token_scopes, sub=identifier)
    except (InvalidTokenError, ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_context_base(
    token_data: TokenData, db: DBSession, account_type: AccountTypeEnum
) -> UserContext:
    user: UserInDB = await get_user(token_data.sub, db, account_type)  # type: ignore
    logger.info(
        f"Fetched user: {user.username if user else 'None'} for account type: {account_type}"
    )
    if not user:
        raise InvalidCredentialsException
    return UserContext(user=user, scopes=token_data.scopes)


async def get_client_context(
    security_scopes: SecurityScopes, credentials: HTTPBearerDependency, db: DBSession
) -> UserContext:
    token_data = await get_token_payload(credentials)
    context = await get_user_context_base(token_data, db, AccountTypeEnum.client)

    for scope in security_scopes.scopes:
        if scope not in context.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return context


async def get_agent_context(
    security_scopes: SecurityScopes, credentials: HTTPBearerDependency, db: DBSession
) -> UserContext:
    token_data = await get_token_payload(credentials)
    print(token_data)
    context = await get_user_context_base(token_data, db, AccountTypeEnum.agent)

    for scope in security_scopes.scopes:
        if scope not in context.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return context


async def user_context(
    security_scopes: SecurityScopes, credentials: HTTPBearerDependency, db: DBSession
) -> UserContext:
    token_data = await get_token_payload(credentials)

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    # Determine account type based on scopes
    account_type = AccountTypeEnum.client
    if AccountTypeEnum.agent.value in token_data.scopes:
        account_type = AccountTypeEnum.agent

    logger.info(f"Account type: {account_type}")

    # Fetch user
    context = await get_user_context_base(token_data, db, account_type)
    user = context.user

    if not user:
        raise InvalidCredentialsException

    logger.info(f"User {user.username} fetched")

    if "admin" in token_data.scopes and user.role == UserRole.ADMIN:
        return UserContext(user=user, scopes=token_data.scopes)

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return UserContext(user=user, scopes=token_data.scopes)


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


GetClientContext = Annotated[UserContext, Depends(get_client_context)]


async def get_current_client(context: GetClientContext):
    if "otp" in context.scopes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP token not permitted in this route",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context.user


GetAgentContext = Annotated[UserContext, Depends(get_agent_context)]


async def get_current_agent(context: GetAgentContext):
    if "otp" in context.scopes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP token not permitted in this route",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context.user


GetUser = Annotated[BaseUser, Depends(get_current_user)]


async def get_current_active_user(current_user: GetUser):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveUser = Annotated[BaseUser, Depends(get_current_active_user)]


async def get_active_verified_user(current_user: ActiveUser):
    if not current_user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unverified user"
        )
    return current_user


ActiveVerifiedUser = Annotated[BaseUser, Depends(get_active_verified_user)]


async def get_current_active_agent(
    current_user: Annotated[BaseUser, Security(get_current_agent, scopes=["agent"])],
):
    if not current_user.is_active and not current_user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveAgent = Annotated[BaseUser, Depends(get_current_active_agent)]


async def active_verified_client(
    current_user: Annotated[BaseUser, Security(get_current_client, scopes=["client"])],
):
    if not current_user.is_active and not current_user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive User"
        )
    return current_user


ActiveVerifiedClient = Annotated[UserInDB, Depends(active_verified_client)]


async def get_verified_otp_email(
    user_context: GetUserContext, credentials: HTTPBearerDependency
):
    token = credentials.credentials

    token_exp = await token_exp_time(token)
    await blacklist_token(token, token_exp)  # type: ignore
    return user_context.user


OtpVerification = Annotated[BaseUser, Security(get_verified_otp_email, scopes=["otp"])]


async def require_admin_scope(
    current_user: Annotated[BaseUser, Security(get_current_user, scopes=["admin"])],
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


AdminUser = Annotated[BaseUser, Depends(require_admin_scope)]

from fastapi import WebSocket, Query


async def get_websocket_user(
    websocket: WebSocket, db: DBSession, token: Annotated[str | None, Query()] = None
):

    logger.info(f"Extracted Token: {token}")
    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]  # type: ignore
        )  # type: ignore
        identifier = payload.get("sub")
        if not identifier:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        user: UserInDB = await get_user(identifier, db)  # type: ignore
        logger.info(f"{user.email} fetched")
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        if not user.is_active or not user.verified:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return user
    except (InvalidTokenError, ExpiredSignatureError) as e:
        logger.error(f"an Error occurred\n{e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


ActiveVerifiedWSUser = Annotated[BaseUser, Depends(get_websocket_user)]


async def reset_password(user: UserInDB, db: DBSession, new_password: str):
    user.password = new_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
