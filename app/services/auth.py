from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Buyer,Seller,BaseUser
from fastapi import status,HTTPException
from sqlalchemy.future import select
from email_validator import validate_email,EmailNotValidError
import re
from core.configs import PHONE_REGEX,redis,BLACKLIST_PREFIX
from app.schemas.auth_schema import LoginData,OtpSchema,Token
from app.schemas.user_schema import UserInDB
from app.utils.utils import verify_password
from datetime import datetime,timezone,timedelta
from core.configs import expire_delta,ALGORITHM,SECRET_KEY, logger
import jwt
from sqlalchemy.exc import IntegrityError
from core.dependecies import VerificationException
from app.schemas.user_schema import BaseUserSchema
from app.utils.email import create_set_send_otp,send_otp_for_signup
from app.utils.utils import verify_otp,blacklist_token,token_exp_time
from app.utils.enums import AccountTypeEnum
from jwt.exceptions import InvalidTokenError

#NOTE - Create Buyer
async def create_buyer(new_user:Buyer,db:AsyncSession):
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f'User {new_user.email} created')
        return new_user  
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail='user already exists')
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))

#NOTE -  Create Seller
async def create_seller(new_user:Seller,db:AsyncSession):
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f'User {new_user.email} created')
        return new_user
    except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail='User already exists')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))



class GetUser:
    def __init__(self, db: AsyncSession, identifier: str):
        self.db = db
        self.identifier = identifier

    def __check_email(self) -> bool:
        """Check if the identifier is a valid email."""
        try:
            validate_email(self.identifier, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    def __validate_phone(self) -> bool:
        """Check if the identifier is a valid phone number."""
        return bool(re.fullmatch(PHONE_REGEX, self.identifier))

    async def get_user(self):
        """Fetch a user based on email, phone, or username."""
        query = select(BaseUser)

        if self.__check_email():
            query = query.where(BaseUser.email == self.identifier)
        elif self.__validate_phone():
            query = query.where(BaseUser.phone_number == self.identifier)
        else:
            query = query.where(BaseUser.username == self.identifier)

        result = await self.db.execute(query)
        new_user = result.scalar_one_or_none() 
        if new_user:
            await self.db.refresh(new_user)
        return new_user
    
    
async def get_user(db:AsyncSession,identifier:str)->BaseUserSchema:
        user_fetcher = GetUser(db, identifier)
        user = await user_fetcher.get_user()
        return user

async def authenticate_user(db:AsyncSession,login_data:LoginData):
    user:UserInDB = await get_user(db,login_data.username)
    if not user:
        return False
    if not verify_password(login_data.password,user.password):
        return False
    return user

async def create_access_token(data:dict,expire_time=None):
    expiration = timedelta(minutes=expire_time) if expire_time else expire_delta
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+ expiration
    to_encode.update({'exp':expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

async def process_signup(user_data:BaseUserSchema):
    #NOTE -  Process OTP
    send_set_otp = await create_set_send_otp(user_data.email,user_data.model_dump())
    if send_set_otp:
        return user_data
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail= 'unable to send confirmation email'
    )
async def process_accnt_verification(payload:OtpSchema,db:AsyncSession):
    user_data = await verify_otp(**payload.model_dump(),sign_up=True)
    if not user_data:
         raise VerificationException
    account_type = user_data.get('account_type')
    if account_type == AccountTypeEnum.buyer:
        user = Buyer(**user_data)
        user.verified=True
        await create_buyer(user,db)
        access_token = await create_access_token(
        data={"sub": user.username}
        )
        logger.info(f'{user.email} Sucessfully verified and created')
        return Token(access_token=access_token, token_type="Bearer")
    
    user = Seller(**user_data)
    user.verified = True
    await create_seller(user,db)
    access_token = await create_access_token(
    data={"sub": user.username}
    )
    return Token(access_token=access_token, token_type="Bearer")

async def process_send_otp(payload:OtpSchema):
    send_otp = await send_otp_for_signup(payload.email)
    if send_otp:
        return {'message':'OTP Resent'}
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail= 'unable to send confirmation email'
    )
    
    
async def proccess_logout(token:str):
    try:
        remaining_time = await token_exp_time(token)
        if not remaining_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        await blacklist_token(token,remaining_time)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return {'message':'Logged out'}


async def process_fgt_pwd(email:str):
    user = await get_user(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='User not found')
    send_set_otp = await create_set_send_otp(email)
    if send_set_otp:
        return {'message':'Password reset otp sent'}
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail= 'unable to send confirmation email'
    )

async def verify_request_otp(email:str,otp:str,db:AsyncSession):
    user = await get_user(db,email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='User not found')
    verified = await verify_otp(email,otp)
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Invalid OTP')
    return True