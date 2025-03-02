from app.schemas.property_schema import PropertyBase
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.property import Property,PropertyImage
from app.schemas.user_schema import UserInDB

async def create_property_listing(current_user:UserInDB,property_data:PropertyBase,db:AsyncSession):
    new_property = Property(user_id=current_user.id,**property_data.model_dump(exclude={'images'}))
    images = [PropertyImage(**img.model_dump()) for img in property_data.images]
    new_property.images = images
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)
    return new_property
    