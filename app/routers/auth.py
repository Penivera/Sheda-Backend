from fastapi import APIRouter,status,HTTPException
from app.schemas.user_schema import UserCreate, UserInDB,UserShow
from app.services.auth import process_signup,process_logout,verify_user as process_accnt_verification
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_access_token,
    switch_account
    )
from core.dependecies import PassWordRequestForm,VerificationException
from core.dependecies import DBSession,TokenDependecy
from app.schemas.auth_schema import (LoginData,
                                     Token,
                                     OtpSchema,
                                     OtpSend,
                                     PasswordReset,
                                     SwitchAccountType, TokenData)
from core.configs import settings,logger
from app.services.user_service import reset_password,OtpVerification,ActiveUser,GetUser
from app.utils.utils import verify_otp,blacklist_token,token_exp_time
from app.utils.email import create_send_otp
from app.schemas.auth_schema import SignUpShow


router = APIRouter(tags=['Auth'],prefix='/auth',)
#NOTE -  fixed user creation response
@router.post('/signup',
             response_model=SignUpShow,
             status_code=status.HTTP_202_ACCEPTED,
             description=settings.SIGN_UP_DESC)
async def signup_user(request:UserCreate,db:DBSession):
    #NOTE - Process signup
    return await process_signup(request,db) # type: ignore # type: ignore

@router.post('/verify-account',response_model=Token,status_code=status.HTTP_201_CREATED)
async def verify_account(email:OtpVerification,db:DBSession):
    return await process_accnt_verification(email,db)

#NOTE - Login Route
@router.post("/login",response_model=Token)
async def login_for_access_token(form_data: PassWordRequestForm) -> Token:
    login_data = LoginData(**form_data.__dict__)
    user:UserInDB= await authenticate_user(login_data)
    logger.info(form_data.scopes)
    scopes = [user.account_type.value,user.role.value] # type: ignore 
    access_token = await create_access_token(
        data=TokenData(sub=user.email,scopes=scopes), # type: ignore
        )
    return Token(access_token=access_token)


@router.post('/logout',status_code=status.HTTP_202_ACCEPTED)
async def logout(current_user:GetUser,token:TokenDependecy):
    return await process_logout(token)



    
@router.put('/reset-password',status_code=status.HTTP_202_ACCEPTED,response_model=Token,description='Reset Password')
async def reset_pwd(current_user:ActiveUser,payload:PasswordReset,email:OtpVerification,db:DBSession):
    await reset_password(current_user,db,payload.password)
    scopes = [current_user.account_type.value] # type: ignore
    token = await create_access_token(data=TokenData(email=email, scopes=scopes)) # type: ignore
    return Token(access_token=token)
        
    
    
@router.post('/send-otp',response_model=dict,status_code=status.HTTP_202_ACCEPTED)
async def send_otp(payload:OtpSend):
    otp_sent = await create_send_otp(payload.email)
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Unable to send OTP'
        )
    return {'detail':'OTP sent'}

verify_otp_desc = '''Token returned from this endpoint is valid for only `5 minutes`
<h3><b>Once the OTP is verified the token is blacklisted</b></h3>
<b><i>These tokens carry a scope that allows only actions that need OTP verification therefore cannot be used elsewhere</i></b>'''

#NOTE - Verification Endpoint
@router.post('/verify-otp',response_model=Token,status_code=status.HTTP_200_OK,description=verify_otp_desc)
async def verify_otp_route(payload:OtpSchema):
    verified = await verify_otp(**payload.model_dump())
    if not verified:
        raise VerificationException
    scopes = ['otp']
    access_token = await create_access_token(
        data=TokenData(sub=payload.email, scopes=scopes), expire_time=5 # type: ignore
    )
    return Token(access_token=access_token)
    
token_refresh_desc ='''This endpoint refreshes a user's token including the neccesary permissions for the account type,in case of <b>unauthorized</b> or <b>account type changes</b>
The previous token will be `blacklisted`'''   

@router.put('/refresh-token',response_model=Token,status_code=status.HTTP_200_OK,description=token_refresh_desc)
async def refresh_token(current_user:ActiveUser,token:TokenDependecy):
    scopes = [current_user.account_type.value] # type: ignore
    token_exp = await token_exp_time(token)
    await blacklist_token(token,token_exp) # type: ignore
    new_token = await create_access_token(data=TokenData(username=current_user.email, scopes=scopes)) # type: ignore
    return Token(access_token=new_token)


#STUB - Switch account type
@router.post('/switch-account',status_code=status.HTTP_200_OK,response_model=Token)
async def switch_account_type(token:TokenDependecy,payload:SwitchAccountType,current_user:ActiveUser):
   
    new_token = await switch_account(payload.switch_to,current_user)
    exp_time = await token_exp_time(token)
    await blacklist_token(token,exp_time) # type: ignore
    return new_token
    








    
    