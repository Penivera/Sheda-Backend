from sqlalchemy.future import select
from sqlalchemy.engine import Result
from app.models.property import Property,PropertyImage
from app.schemas.user_schema import UserInDB
from app.models.property import Property
from app.models.user import BaseUser
from app.schemas.property_schema import PropertyBase,PropertyUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException,status
from app.schemas.property_schema import FilterParams,PropertyFeed,DeleteProperty

async def create_property_listing(current_user:UserInDB,property_data:PropertyBase,db:AsyncSession):
    new_property = Property(user_id=current_user.id,**property_data.model_dump(exclude={'images'}))
    images = [PropertyImage(**img.model_dump()) for img in property_data.images]
    new_property.images = images
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)
    return new_property
    
    
async def get_user_properties(current_user:UserInDB,db:AsyncSession):
    query = select(Property).where(Property.user_id == current_user.id)
    result:Result = await db.execute(query)
    property = result.scalars().all()
    return property

async def update_listing(property_id:int,current_user:UserInDB,update_data:PropertyUpdate,db:AsyncSession):
    property = next(
        (listing for listing in current_user.listing if listing.id == property_id),
        None
    )
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    for key,value in update_data.model_dump(exclude_unset=True,exclude={'images'}).items():
        setattr(property,key,value)
        
    if update_data.images is not None:
    #NOTE  Convert dictionaries to PropertyImage instances
        property_images = [
            PropertyImage(**image_data.model_dump()) for image_data in update_data.images
        ]
    property.images = property_images
    db.add(property)
    await db.commit()
    await db.refresh(property)
    return property

async def filtered_property(filter_query:FilterParams,db:AsyncSession):
    query = select(Property).where(Property.id >= filter_query.cursor).limit(filter_query.limit)
    result:Result = await db.execute(query)
    properties:Property = result.scalars().all()
    next_cursor = properties[-1].id + 1 if properties else None
    return PropertyFeed(data=properties,next_coursor=next_cursor)

async def get_agent_by_id(agent_id:int,db:AsyncSession):
    query = select(BaseUser).where(BaseUser.id == agent_id)
    result:Result =await db.execute(query)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'agent with id:{agent_id} not found'
        )
    await db.refresh(agent)
    return agent
    

async def delist_property(property_id:int,db:AsyncSession,current_user:UserInDB):
    property = next((property for property in current_user.listing if property.id == property_id),None)
    
    if not property:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail='Property not found or you are not the owner'
        )
    await db.delete(property)
    await db.commit()
    return DeleteProperty(message='Property Deleted')
    
    
    
    