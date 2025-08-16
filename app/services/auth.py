from os import access
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import BaseUser,Client,Agent
from fastapi import status,HTTPException
from sqlalchemy.future import select
from email_validator import validate_email,EmailNotValidError
import re
from app.schemas.auth_schema import LoginData,OtpSchema,Token,TokenData,SignUpShow
from app.schemas.user_schema import UserInDB,UserCreate,UserShow
from app.utils.utils import verify_password
from datetime import datetime,timezone,timedelta
from core.configs import settings,logger,redis
import jwt
from sqlalchemy.exc import IntegrityError
from core.dependecies import InvalidCredentialsException
from app.schemas.user_schema import BaseUserSchema,UserCreate
from app.utils.email import create_send_otp
from app.utils.utils import blacklist_token,token_exp_time
from app.utils.enums import AccountTypeEnum
from jwt.exceptions import InvalidTokenError,ExpiredSignatureError
from core.database import AsyncSessionLocal, Base
from datetime import datetime
from pydantic import EmailStr


#NOTE -  Create agent
async def create_account(user_data:UserCreate,db:AsyncSession):
    new_client = Client(**user_data.model_dump(),account_type=AccountTypeEnum.client)
    new_agent = Agent(**user_data.model_dump(),account_type=AccountTypeEnum.agent)
    try:
        db.add(new_client)
        db.add(new_agent)
        await db.commit()
        await db.refresh(new_client)
        await db.refresh(new_agent)
        logger.info(f'User {new_client.email} created') # type:ignore
        return new_client
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
        return bool(re.fullmatch(settings.PHONE_REGEX, self.identifier))

    async def get_user(self,account_type):
        """Fetch a user based on email, phone, or username and account type."""
        async with AsyncSessionLocal() as db:
            query = select(BaseUser)

            if self.__check_email():
                query = query.where(
                    BaseUser.email == self.identifier,
                    BaseUser.account_type == account_type
                    )
            elif self.__validate_phone():
                query = query.where(
                    BaseUser.phone_number == self.identifier,
                    BaseUser.account_type == account_type
                    )
            else:
                query = query.where(
                    BaseUser.username == self.identifier,
                    BaseUser.account_type == account_type)
            
            result = await db.execute(query)
            user = result.scalar_one_or_none() 
            if user:
                user.last_seen = datetime.now()
                await db.commit()
                await db.refresh(user)
                return user
        logger.info('User not found')
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail='User not found'
        )
                

    
    
async def get_user(identifier:str,account_type:AccountTypeEnum=AccountTypeEnum.client)->BaseUserSchema:
    user_fetcher = GetUser(identifier)
    user:UserInDB = await user_fetcher.get_user(account_type)
    return user

async def authenticate_user(login_data:LoginData):
    user:UserInDB = await get_user(login_data.username) # type: ignore
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Username")
    if not verify_password(login_data.password,user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Password")
    return user

async def create_access_token(data:TokenData,expire_time=None):
    expiration = timedelta(minutes=expire_time) if expire_time else settings.expire_delta
    to_encode = data.model_dump().copy()
    expire = datetime.now(timezone.utc)+ expiration
    to_encode.update({'exp':expire})
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM) # type: ignore
    return encoded_jwt

async def process_signup(user_data:UserCreate,db:AsyncSession):
    new_user = await create_account(user_data,db)
    token_data = TokenData(sub=new_user.email, scopes=[new_user.account_type.value]) # type: ignore
    access_token = await create_access_token(data=token_data)
    return SignUpShow(token=Token(access_token=access_token), user_data=UserShow.model_validate(new_user))

async def verify_user(email: EmailStr, db: AsyncSession):
    # Fetch the user
    result = await db.execute(select(BaseUser).where(BaseUser.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    #NOTE - Update the verified field
    user.verified = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def process_logout(token:str):
    try:
        remaining_time = await token_exp_time(token)
        if not remaining_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        await blacklist_token(token,remaining_time)
    except (InvalidTokenError,ExpiredSignatureError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return {'message':'Logged out'}

#NOTE -  Return new token with the neccesarry account type
async def switch_account(switch_to:AccountTypeEnum,current_user:UserInDB):
    user = await get_user(current_user.email,switch_to) # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = f'{switch_to} account not found'
        )
    scopes = [switch_to]
    new_token = await create_access_token(data=TokenData(sub=current_user.email, scopes=scopes)) # type: ignore
    return Token(access_token=new_token)



