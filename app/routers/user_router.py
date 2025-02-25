from fastapi import APIRouter,UploadFile,File,HTTPException,status
from app.services.user_service import GetCurrentActUSer,get_current_user
from app.services.profile import upload_image,reset_password
from core.dependecies import FileUploadException,DBSession,TokenDependecy
from app.schemas.user_schema import PasswordReset
from app.schemas.auth_schema import Token
from app.services.auth import create_access_token
from app.utils.utils import blacklist_token,token_exp_time



router = APIRouter(tags=['Profile'],prefix='/profile',)

#NOTE - Upload Profile Picture
@router.put('/upload-pfp',response_model=dict,description='Add max size 500kb - 2MB',status_code=status.HTTP_202_ACCEPTED)
async def upload_pfp(*,current_user:GetCurrentActUSer,file: UploadFile = File(...),db:DBSession):
    if not file.filename:
        raise FileUploadException
    file_url = await upload_image(file,current_user,db)
    return {'filename': file_url}


@router.put('/reset-pwd',status_code=status.HTTP_202_ACCEPTED,response_model=Token,description='Reset Password')
async def reset_pwd(payload:PasswordReset,token:TokenDependecy,db:DBSession):
    current_user = await get_current_user(token)

    remaining_time = await token_exp_time(token)
    if not remaining_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired token")
    await blacklist_token(token,remaining_time)
    await reset_password(current_user,db,payload.password)
    token = await create_access_token(data={"sub": current_user.username})
    return Token(access_token=token)
    