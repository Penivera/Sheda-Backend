from pydantic import BaseModel,AnyUrl,Field
from typing import List,Union,Annotated,Optional
from app.utils.enums import ListingTypeEnum,PropertyTypeEnum,PropertyStatEnum
from datetime import datetime,time
from app.utils.enums import AppointmentStatEnum

class PropertyImage(BaseModel):
    image_url:Annotated[Union[AnyUrl,str],Field(examples=['https://example/img/property.jpg'],max_length=255)]
    is_primary:Optional[bool] = False
    class Config:
        from_attributes = True

class PropertyBase(BaseModel):
    title:str
    description:str
    location:str
    price: float
    property_type:PropertyTypeEnum
    listing_type:ListingTypeEnum
    status:PropertyStatEnum
    furnished:bool
    is_active:bool
    bathroom:int
    bedroom:int
    air_condition:bool
    pop_ceiling:bool
    floor_tiles:bool
    running_water:bool
    furniture:bool
    prepaid_meter:bool
    wifi:bool
    is_negotiable:bool
    images:List[PropertyImage]
    
    class Config:
        from_attributes = True
        
class PropertyShow(PropertyBase):
    id:int
    agent_id:int
    
    class Config:
        from_attributes = True
        
        
class PropertyUpdate(BaseModel):
    title:Optional[str] = None
    description:Optional[str] = None
    location:Optional[str] = None
    price: Optional[float]= None
    property_type:Optional[PropertyTypeEnum]= None
    listing_type:Optional[ListingTypeEnum] = None
    status:Optional[PropertyStatEnum] = None
    furnished:Optional[bool] = None
    is_active:Optional[bool] = None
    bathroom:Optional[int] = None
    bedroom:Optional[int] = None
    air_condition:Optional[bool] = None
    pop_ceiling:Optional[bool] = None
    floor_tiles:Optional[bool] = None
    running_water:Optional[bool] = None
    furniture:Optional[bool] = None
    prepaid_meter:Optional[bool] = None
    wifi:Optional[bool] = None
    is_negotiable:Optional[bool] = None
    images:Optional[List[PropertyImage]] = None
    
    class Config:
        from_attributes = True
        
class FilterParams(BaseModel):
    limit: Annotated[int,Field(description='The amount of listings to fetch',ge=10,default=20)]
    cursor:Annotated[int,Field(description='The Id of the last listing',ge=1,default=1)]

class PropertyFeed(BaseModel):
    data:List[PropertyShow]
    next_coursor:int|None
    
class DeleteProperty(BaseModel):
    message:str


class AgentAvailabilitySchema(BaseModel):
    weekday:Annotated[str ,Field(..., example="MONDAY")]  # Store as uppercase string
    start_time: Annotated[time, Field(..., example="09:00",description='HH:MM format')]  # HH:MM format
    end_time: Annotated[time,Field(..., example="17:00")]
    
class AppointmentSchema(BaseModel):
    agent_id:int
    property_id:int
    requested_time:datetime
    
class AvailabilityShow(AgentAvailabilitySchema):
    id:int
    agent_id:int
    is_booked:bool
    
    class Config:
        from_attributes = True

class AppointmentShow(BaseModel):
    id:int
    client_id:int
    agent_id:int
    property_id:int
    scheduled_at:datetime
    status:AppointmentStatEnum
    created_at:datetime
    updated_at:datetime
    

class ContractInDB(BaseModel):
    id: int
    property_id: int 
    client_id: int
    agent_id:int
    contract_type: str
    amount: float
    start_date: datetime
    end_date: datetime | None
    is_active: bool 
    property:PropertyShow 
    
    class Config:
        from_attributes = True
        
class ContractCreate(BaseModel):
    property_id: int
    amount: float
    rental_period_months: Optional[int] = None  # Required only for rentals
    is_payment_made: bool  # Ensure payment is confirmed before contract creation

class ContractResponse(BaseModel):
    contract_id: int
    property_id: int
    contract_type: ListingTypeEnum
    amount: float
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True