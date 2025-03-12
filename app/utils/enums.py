from pydantic import BaseModel,Field
from enum import Enum 
from typing import Annotated
from core.configs import PHONE_REGEX
from typing import Literal
#NOTE -  Custom datatype for Phone numbers
PhoneStr = Annotated[str,Field(
    examples=['+2348078417891',],
    description='Phone number in international format',
    pattern=PHONE_REGEX,
    min_length=10,
    max_length=15,
)]

class AccountTypeEnum(str,Enum):
    client = 'client'
    agent = 'agent'
    
class KycStatusEnum(str,Enum):
    pending = 'pending'
    verified = 'verified'
    rejected = 'rejected'
    
    
class PropertyStatEnum(str,Enum):
    rent ='rent'
    sale = 'sale'
    
    
class PropertyTypeEnum(str,Enum):
    apartment = 'apartment'
    land = 'land'
    
class AppointmentStatEnum(str,Enum):
    pending = "pending"
    confirmed = "confirmed" 
    canceled = "canceled"
    
    

    

