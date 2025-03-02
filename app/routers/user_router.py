from fastapi import APIRouter,UploadFile,File,HTTPException,status
from app.services.user_service import GetCurrentActUSer
from app.services.profile import upload_image,update_pfp,update_user
from core.dependecies import FileUploadException,DBSession
from app.schemas.user_schema import UserShow,UserUpdate,FileShow,FileDir





router = APIRouter(tags=['User'],prefix='/user',)

#NOTE - Upload Profile Picture
@router.put('/file-upload/{type}',response_model=FileShow,description='Add max size 500kb - 2MB',status_code=status.HTTP_202_ACCEPTED)
async def upload_file(type:FileDir,current_user:GetCurrentActUSer,file: UploadFile = File(...)):
    if not file.filename:
        raise FileUploadException
    file_url = await upload_image(file,current_user.email,type)
    return FileShow(file_url=file_url)


#NOTE -  Get the current user data
@router.get('/me',response_model=UserShow,description='Get Current User Profile',status_code=status.HTTP_200_OK)
async def get_me(current_user:GetCurrentActUSer):
    return current_user


#NOTE - Update User Profile
@router.put('/update/me',response_model=UserUpdate,description='Update User Profile',status_code=status.HTTP_202_ACCEPTED)
async def update_me(current_user:GetCurrentActUSer,update_data:UserUpdate,db:DBSession):
    return await update_user(update_data,db,current_user)


#NOTE - Delete

@router.delete('/delete-accnt',status_code=status.HTTP_202_ACCEPTED)
async def delete_account(current_user:GetCurrentActUSer,db:DBSession):
    current_user.is_active =False
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
