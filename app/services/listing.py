from app.schemas.property_schema import PropertyBase
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.property import Property,PropertyImage
from app.schemas.user_schema import UserShow

async def create_property_listing(current_user:UserShow,property_data:PropertyBase,db:AsyncSession):
    new_property = Property(**property_data.model_dump())
    for i,image_url in enumerate(property_data.images):
        is_primary = i == 0
        new_image = PropertyImage(**image_url.model_dump(),is_primary=is_primary)
        new_property.images.append(new_image)
    current_user.properties.append(new_property)
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)
    return new_property
    