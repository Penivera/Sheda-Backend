from pydantic import (BaseModel,
                      BeforeValidator,
                      EmailStr,
                      Field,)
from typing import Optional,Annotated
from  app.utils.enums import PhoneStr,AccountTypeEnum
from app.utils.utils import hash_password
from typing import Optional
from typing import Annotated
from datetime import datetime
from app.utils.enums import KycStatusEnum

#NOTE - Base User Schema and response schema
class BaseUserSchema(BaseModel):
    profile_pic : Annotated[Optional[str],Field(examples=['https://example/img/user.jpg'],max_length=255)]=None
    username:Annotated[Optional[str],Field(example='username',default='Admin',max_length=30)]
    email: Annotated[EmailStr,Field(examples=['penivera655@gmail.com'])]
    phone_number:Optional[PhoneStr]
    account_type:AccountTypeEnum
    fullname:str
    agency_name:Optional[str]
    location:Optional[str]=None
        
class BuyerCreate(BaseUserSchema):
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
class SellerCreate(BaseUserSchema):
    account_type:Annotated[AccountTypeEnum,Field(examples=['seller'])]
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
    
class UserShow(BaseUserSchema):
    is_active:bool
    created_at:datetime
    updated_at:datetime
    verified:bool
    location:str
    kyc_status: KycStatusEnum
    class config:
        from_attributes = True
    
class UserInDB(UserShow):
    account_type:AccountTypeEnum
    password:str
    
class UserUpdate(BaseUserSchema):
    Kyc_status:KycStatusEnum
    password:Annotated[Optional[str],BeforeValidator(hash_password),Field(examples=['admin'])]
    class config:
        from_attributes = True
    