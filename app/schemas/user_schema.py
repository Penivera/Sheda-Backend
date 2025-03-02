from pydantic import (BaseModel,
                      BeforeValidator,
                      AfterValidator,
                      EmailStr,
                      Field,AnyUrl)
from typing import Optional,Annotated
from  app.utils.enums import PhoneStr,AccountTypeEnum
from app.utils.utils import hash_password,decode_url
from typing import Optional
from typing import Annotated
from datetime import datetime
from app.utils.enums import KycStatusEnum
from typing import Union,Literal,List
from app.schemas.property_schema import PropertyShow

#NOTE - Base User Schema and response schema
class BaseUserSchema(BaseModel):
    profile_pic : Annotated[Optional[Union[AnyUrl,str]],AfterValidator(decode_url),Field(examples=['https://example/img/user.jpg'],max_length=255)]=None
    username:Annotated[Optional[str],Field(example='Admin',max_length=30)] = None
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])] = None
    phone_number:Optional[PhoneStr] = None
    account_type:Optional[AccountTypeEnum] = None
    fullname:Optional[str] = None
    agency_name:Optional[str] = None
    location:Optional[str] = None
    
    class Config:
        from_attributes = True
        
class BuyerCreate(BaseUserSchema):
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])]
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
class SellerCreate(BaseUserSchema):
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])]
    account_type:Annotated[AccountTypeEnum,Field(examples=['seller'])]
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
    
class UserShow(BaseUserSchema):
    is_active:bool
    created_at:datetime
    updated_at:datetime
    verified:bool
    location:str
    kyc_status: KycStatusEnum
    listing:Optional[List[PropertyShow]] = None
    class Config:
        from_attributes = True
    
class UserInDB(UserShow):
    id:int
    account_type:AccountTypeEnum
    password:str
    
class UserUpdate(BaseUserSchema):
    Kyc_status:Optional[KycStatusEnum] = None

    class Config:
        from_attributes = True
        
        
class FileShow(BaseModel):
    file_url:str
    class Config:
        from_attributes = True
        

    
FileDir = Literal['profile','property']

class SellerFeed(BaseModel):
    profile_pic: Union[AnyUrl,str] = None
    username:str
    email:EmailStr
    phone_number:PhoneStr
    agency_name:str
    location:str
    kyc_status:KycStatusEnum
    last_seen: datetime
    rating:float
    listing:List[PropertyShow] = []
    
    class Config:
        from_attributes = True
        
        
class RatingShow(BaseModel):
    rating:float
    
    class Config:
        from_attributes = True
