from pydantic import BaseModel,EmailStr,Field
from app.utils.enums import PhoneStr,AccountTypeEnum,KycStatusEnum
from app.schemas.user_schema import BaseUserSchema
from datetime import datetime
from typing import Union,Optional,Annotated

class TokenData(BaseModel):
    username:Union[str,EmailStr,PhoneStr]
    
class LoginData(BaseModel):
    username:Union[EmailStr,PhoneStr,str]
    password:str
    
class Token(BaseModel):
    access_token:str
    token_type:Optional[str] = 'Bearer'
    
class BuyerLogin(BaseModel):
    email:Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
    password:str
    
class User(BaseUserSchema):
    is_active:bool
    created_at:datetime
    updated_at:datetime
    verified:bool
    location:str
    access_token:Optional[Token] =None
    class config:
        from_attributes = True
    
class UserInDB(User):
    account_type:AccountTypeEnum
    password:str
    
    class config:
        from_attributes = True

class OtpSchema(BaseModel):
    email:Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
    otp:Union[str,int]
    
#NOTE -  For Resend otp  
class OtpResendSchema(BaseModel):
    email:Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
    
        
