from pydantic import BaseModel,EmailStr,Field,BeforeValidator
from app.utils.enums import PhoneStr
from typing import Union,Optional,Annotated
from app.utils.utils import hash_password


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


class OtpSchema(BaseModel):
    email:Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
    otp:Union[str,int]
    
#NOTE -  For Resend otp  
class OtpSend(BaseModel):
    email:Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
class PasswordReset(BaseModel):
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
        
