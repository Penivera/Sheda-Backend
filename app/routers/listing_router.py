from fastapi import APIRouter,UploadFile,File,HTTPException,status
from core.dependecies import FileUploadException,DBSession
from app.schemas.property_schema import PropertyBase,PropertyShow,PropertyUpdate,FilterParams,PropertyFeed,DeleteProperty
from app.services.listing import (create_property_listing,
                                  get_user_properties,
                                  update_listing,
                                  filtered_property,
                                  get_seller_by_id,
                                  delist_property
                                  )
from app.services.user_service import ActiveSeller,ActiveUser
from app.schemas.user_schema import SellerFeed
from typing import List,Annotated
from fastapi import Query


router = APIRouter(prefix='/property',tags=['Property'],)

@router.post('/list-property',response_model=PropertyShow,description='Upload Property',status_code=status.HTTP_201_CREATED)
async def list_property(current_user:ActiveSeller,payload:PropertyBase,db:DBSession):
    return await create_property_listing(current_user,payload,db)

@router.get('/me',response_model=List[PropertyShow],status_code=status.HTTP_200_OK)
async def get_my_listing(current_user:ActiveSeller,db:DBSession):
    return await get_user_properties(current_user,db)


@router.put('/update/{property_id}',response_model=PropertyShow,
            status_code= status.HTTP_202_ACCEPTED)
async def edit_property_listing(property_id:int,update_data:PropertyUpdate,current_user:ActiveSeller,db:DBSession):
    return await update_listing(property_id,current_user,update_data,db)
    
   
list_desc ='''  
Retrieve a paginated list of available properties using cursor-based pagination. Users can filter results based on specific criteria, such as property ID, and define the number of listings returned per request. The response includes a `next_cursor` to facilitate seamless pagination.'''  
    
@router.get('/get-properties',response_model=PropertyFeed,status_code=status.HTTP_200_OK,description=list_desc)
async def property_feed(filter_query:Annotated[FilterParams,Query()],current_user:ActiveUser,db:DBSession):
    return await filtered_property(filter_query,db)

@router.get('/seller-profile{seller_id}',response_model=SellerFeed,status_code=status.HTTP_200_OK)
async def seller_profile(seller_id:int,current_user:ActiveUser,db:DBSession):
    return await get_seller_by_id(seller_id,db)

@router.delete('/delete/{property_id}',status_code=status.HTTP_202_ACCEPTED,response_model = DeleteProperty)
async def delete_property(property_id:int,current_user:ActiveSeller,db:DBSession):
    return await delist_property(property_id,db,current_user)
    