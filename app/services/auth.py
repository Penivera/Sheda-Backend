from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import BaseUser,Client,Agent
from fastapi import status,HTTPException
from sqlalchemy.future import select
from email_validator import validate_email,EmailNotValidError
import re
from core.configs import PHONE_REGEX
from app.schemas.auth_schema import LoginData,OtpSchema,Token
from app.schemas.user_schema import UserInDB
from app.utils.utils import verify_password
from datetime import datetime,timezone,timedelta
from core.configs import expire_delta,ALGORITHM,SECRET_KEY, logger,user_data_prefix,redis
import jwt
from sqlalchemy.exc import IntegrityError
from core.dependecies import InvalidCredentialsException
from app.schemas.user_schema import BaseUserSchema
from app.utils.email import create_send_otp
from app.utils.utils import blacklist_token,token_exp_time
from app.utils.enums import AccountTypeEnum
from jwt.exceptions import InvalidTokenError
from core.database import AsyncSessionLocal
from datetime import datetime
from pydantic import EmailStr


#NOTE -  Create agent
async def create_account(new_user:BaseUser,db:AsyncSession):
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
    def __init__(self, identifier: str):
        #self.db = db
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
        async with AsyncSessionLocal() as db:
            query = select(BaseUser)

            if self.__check_email():
                query = query.where(BaseUser.email == self.identifier)
            elif self.__validate_phone():
                query = query.where(BaseUser.phone_number == self.identifier)
            else:
                query = query.where(BaseUser.username == self.identifier)
            
            result = await db.execute(query)
            user = result.scalar_one_or_none() 
            if user:
                user.last_seen = datetime.now()
                await db.commit()
                await db.refresh(user)
                return user
                

    
    
async def get_user(identifier:str)->BaseUserSchema:
    user_fetcher = GetUser(identifier)
    user = await user_fetcher.get_user()
    return user

async def authenticate_user(login_data:LoginData):
    user:UserInDB = await get_user(login_data.username)
    if not user:
        raise InvalidCredentialsException
    if not verify_password(login_data.password,user.password):
        raise InvalidCredentialsException
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
    await redis.hset(user_data_prefix.format(user_data.email),mapping=user_data.model_dump(exclude_none=True,exclude_unset=True))
    
    logger.info('User data set to redis')
    await redis.expire(user_data_prefix.format(user_data.email),timedelta(hours=2))
    
    logger.info('timer set on user data 2 hours')
    send_set_otp = await create_send_otp(user_data.email)
    
    if not send_set_otp:
        raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail= 'unable to send confirmation email')
        
    return user_data
    
async def process_accnt_verification(key:EmailStr,db:AsyncSession):
    user_data = await redis.hgetall(user_data_prefix.format(key))
    user_data ={key.decode():value.decode() for key,value in user_data.items()}
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_205_RESET_CONTENT,
            detail='User data not found or expired'
        )
    logger.info(f'{key} Data retrieved from redis')
    await redis.delete(user_data_prefix.format(key))
    
    if user_data.get('account_type') == AccountTypeEnum.agent:
        new_user = Agent(**user_data)
    else:
        new_user = Client(**user_data)
    await create_account(new_user,db)
    scopes = [new_user.account_type.value]
    access_token = await create_access_token(
        data={"sub": new_user.username,"scopes": scopes}
        )
    return Token(access_token=access_token, token_type="Bearer")
    
    
async def proccess_logout(token:str):
    try:
        remaining_time = await token_exp_time(token)
        if not remaining_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        await blacklist_token(token,remaining_time)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return {'message':'Logged out'}




