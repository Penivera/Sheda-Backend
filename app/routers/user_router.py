from fastapi import APIRouter,UploadFile,File,HTTPException,status
from app.services.user_service import ActiveUser,ActiveClient,ActiveAgent
from app.services.profile import upload_image,update_user
from core.dependecies import FileUploadException,DBSession
from app.schemas.user_schema import UserShow,UserUpdate,FileShow,FileDir
from typing import Annotated,List
from sqlalchemy.engine import Result
from app.schemas.property_schema import (AppointmentSchema,
                                         AppointmentShow,
                                         AvailabilityShow,
                                         AgentAvailabilitySchema)
from app.services.listing import book_appointment,create_availability,fetch_schedule,update_agent_availabilty




router = APIRouter(tags=['User'],prefix='/user',)

#NOTE - Upload Profile Picture
@router.put('/file-upload/{type}',response_model=FileShow,description='Add max size 500kb - 2MB',status_code=status.HTTP_202_ACCEPTED)
async def upload_file(type:FileDir,current_user:ActiveUser,file: UploadFile = File(...)):
    if not file.filename:
        raise FileUploadException
    file_url = await upload_image(file,current_user.email,type)
    return FileShow(file_url=file_url)


#NOTE -  Get the current user data
@router.get('/me',response_model=UserShow,description='Get Current User Profile',status_code=status.HTTP_200_OK)
async def get_me(current_user:ActiveUser):
    return current_user

update_desc='''pick the target field and exclude the rest,
the server will dynamically update,all fields are optional'''
#NOTE - Update User Profile
@router.put('/update/me',response_model=UserUpdate,description=update_desc,status_code=status.HTTP_202_ACCEPTED)
async def update_me(current_user:ActiveUser,update_data:UserUpdate,db:DBSession):
    return await update_user(update_data,db,current_user)


#NOTE - Delete

@router.delete('/delete-accnt',status_code=status.HTTP_202_ACCEPTED)
async def delete_account(current_user:ActiveUser,db:DBSession):
    current_user.is_active =False
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    

#NOTE Get agent availability
@router.get("/book-appointment",response_model=status.HTTP_200_OK,response_model= AppointmentShow)
async def book_appointment(current_user:ActiveClient,payload:AppointmentSchema,db:DBSession):
    return await book_appointment(current_user.id,payload.agent_id,payload.requested_time,db)

#NOTE create availability
@router.post('/create-available-time',status_code=status.HTTP_201_CREATED,response_model=AvailabilityShow)
async def create_schedule(request:AgentAvailabilitySchema,current_user:ActiveAgent,db:DBSession):
    return await create_availability(request,db,current_user)

@router.get('/get-schedule/me',status_code=status.HTTP_200_OK,response_model=List[AvailabilityShow])
async def get_schedule(current_user:ActiveAgent,db:DBSession):
    return await fetch_schedule(current_user.id,db)

@router.put('/update-schedule/{id}',response_model=AvailabilityShow,status_code=status.HTTP_200_OK)
async def update_schedule(id:int,update_data:AgentAvailabilitySchema,current_user:ActiveAgent,db:DBSession):
    return await update_agent_availabilty(update_data,db,id)