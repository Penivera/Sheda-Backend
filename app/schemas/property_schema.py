from pydantic import BaseModel,AnyUrl,Field
from typing import List,Union,Annotated
from app.utils.enums import PropertyStatEnum,PropertyTypeEnum

class PropertyImage(BaseModel):
    image_url:Annotated[Union[AnyUrl,str],Field(examples=['https://example/img/property.jpg'],max_length=255)]
    is_primary:bool
    class config:
        from_attributes = True

class PropertyBase(BaseModel):
    title:str
    description:str
    location:str
    price: float
    property_type:PropertyTypeEnum
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
    images:List[PropertyImage]
    is_negotiable:bool
    
    class config:
        from_attributes = True
        
class PropertyShow(PropertyBase):
    id:int
    user_id:int