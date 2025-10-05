from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import BaseUser, Client, Agent
from fastapi import status, HTTPException
from sqlalchemy.future import select
from email_validator import validate_email, EmailNotValidError
import re
from app.schemas.auth_schema import LoginData, Token, TokenData, SignUpShow
from app.schemas.user_schema import UserInDB, UserCreate, UserShow
from app.utils.utils import verify_password
from datetime import datetime, timezone, timedelta
from core.configs import settings
from core.dependecies import DBSession
from core.logger import logger
import jwt
from sqlalchemy.exc import IntegrityError
from app.schemas.user_schema import BaseUserSchema
from app.utils.utils import blacklist_token, token_exp_time
from app.utils.enums import AccountTypeEnum
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from core.database import AsyncSessionLocal
from pydantic import EmailStr
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload

# NOTE -  Create agent
async def create_account(user_data: UserCreate, db: AsyncSession):
    new_client = Client(**user_data.model_dump(), account_type=AccountTypeEnum.client)
    new_agent = Agent(**user_data.model_dump(), account_type=AccountTypeEnum.agent)
    try:
        db.add_all([new_client, new_agent])
        await db.commit()
        await db.refresh(new_client)
        await db.refresh(new_agent)
        logger.info(f"User {new_client.email} created")  # type:ignore
        return new_client
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )




async def get_user(identifier: str, db: AsyncSession,account_type=AccountTypeEnum.client) -> BaseUserSchema:
    """Fetch a user based on email, phone, or username and account type."""

    query = (
        select(BaseUser)
        .where(
            and_(
                BaseUser.account_type == account_type,
                or_(
                    BaseUser.email == identifier,
                    BaseUser.username == identifier,
                    BaseUser.phone_number == identifier
                )
            )
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user:
        user.last_seen = datetime.now()
        await db.commit()
        await db.refresh(user)
    return user or None
    







async def authenticate_user(login_data: LoginData,db: AsyncSession) -> UserInDB:
    user: UserInDB = await get_user(login_data.username, db)  # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Username"
        )
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Password"
        )
    return user


async def create_access_token(data: TokenData, expire_time=None):
    expiration = (
        timedelta(minutes=expire_time) if expire_time else settings.expire_delta
    )
    to_encode = data.model_dump().copy()
    expire = datetime.now(timezone.utc) + expiration
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )  # type: ignore
    return encoded_jwt


async def process_signup(user_data: UserCreate, db: AsyncSession):
    new_user = await create_account(user_data, db)
    token_data = TokenData(sub=new_user.email, scopes=[new_user.account_type.value])  # type: ignore
    access_token = await create_access_token(data=token_data)
    return SignUpShow(
        token=Token(access_token=access_token),
        user_data=UserShow.model_validate(new_user),
    )


async def verify_user(email: EmailStr, db: AsyncSession):
    # Fetch the user
    result = await db.execute(select(BaseUser).where(BaseUser.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # NOTE - Update the verified field
    user.verified = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def process_logout(token: str):
    try:
        remaining_time = await token_exp_time(token)
        if not remaining_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

        await blacklist_token(token, remaining_time)
    except (InvalidTokenError, ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    return {"message": "Logged out"}


# NOTE -  Return new token with the neccesarry account type
async def switch_account(switch_to: AccountTypeEnum, current_user: UserInDB):
    user = await get_user(current_user.email, switch_to)  # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{switch_to} account not found",
        )
    scopes = [switch_to]
    new_token = await create_access_token(
        data=TokenData(sub=current_user.email, scopes=scopes) # type: ignore
    )  # type: ignore
    return Token(access_token=new_token)
