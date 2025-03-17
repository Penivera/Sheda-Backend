from pydantic import (BaseModel,
                      BeforeValidator,
                      AfterValidator,
                      EmailStr,
                      Field,AnyUrl)
from  app.utils.enums import PhoneStr,AccountTypeEnum
from app.utils.utils import hash_password,decode_url
from datetime import datetime
from app.utils.enums import KycStatusEnum
from typing import Union,Literal,List,Optional,Annotated
from app.schemas.property_schema import PropertyShow,AvailabilityShow,ContractInDB,AppointmentShow

#NOTE - Base User Schema and response schema
class BaseUserSchema(BaseModel):
    profile_pic : Annotated[Optional[Union[AnyUrl,str]],AfterValidator(decode_url),Field(examples=['https://example/img/user.jpg'],max_length=255)]=None
    username:Annotated[Optional[str],Field(example='Admin',max_length=30)] = None
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])] = None
    phone_number:Optional[PhoneStr] = None
    account_type:Optional[AccountTypeEnum] = AccountTypeEnum.client
    fullname:Optional[str] = None
    location:Optional[str] = None
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username:Annotated[Optional[str],Field(example='Admin',max_length=30)] = None
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])]
    password:Annotated[str,BeforeValidator(hash_password),Field(examples=['admin'])]
    
class AccountInfoBase(BaseModel):
    account_name:Optional[str] = None
    bank_name:Optional[str] = None
    acount_number:Annotated[Optional[str],Field(examples=['1234567890'],max_length=20,default=None)]

class AccountInfoShow(AccountInfoBase):
    id:int
    user_id:int
    
    class Config:
        from_attributes = True
    
    
class UserShow(BaseUserSchema):
    agency_name:Annotated[Optional[str],Field(default=None)]
    is_active:bool
    created_at:datetime
    updated_at:datetime
    verified:bool
    location:Optional[str]
    kyc_status: KycStatusEnum
    listing:Optional[List[PropertyShow]] = []
    appointments: Optional[List[AppointmentShow]]=[]
    account_info:Optional[List[AccountInfoShow]]  = []
    availabilities:Optional[List[AvailabilityShow]] = []
    class Config:
        from_attributes = True
    

class UserInDB(UserShow):
    id:int
    account_type:AccountTypeEnum
    password:str
    
class UserUpdate(BaseUserSchema):
    profile_pic : Annotated[Optional[Union[AnyUrl,str]],AfterValidator(decode_url),Field(examples=['https://example/img/user.jpg'],max_length=255)]=None
    username:Annotated[Optional[str],Field(example='Admin',max_length=30)] = None
    email: Annotated[Optional[EmailStr],Field(examples=['penivera655@gmail.com'])] = None
    phone_number:Optional[PhoneStr] = None
    fullname:Optional[str] = None
    location:Optional[str] = None
    account_type:Optional[AccountTypeEnum] = None
    kyc_status:Optional[KycStatusEnum] = None

    class Config:
        from_attributes = True
        
        
class FileShow(BaseModel):
    file_url:str
    class Config:
        from_attributes = True
        

    
FileDir = Literal['profile','property']

class AgentFeed(BaseModel):
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
    availbilities:List[AvailabilityShow] = []
    
    class Config:
        from_attributes = True
        
        
class RatingShow(BaseModel):
    rating:float
    
    class Config:
        from_attributes = True

