from fastapi import APIRouter,status,HTTPException
from app.schemas.user_schema import UserCreate,UserShow,BaseUserSchema
from app.services.auth import process_signup,process_accnt_verification,proccess_logout
from app.services.auth import authenticate_user,create_access_token
from core.dependecies import PassWordRequestForm,VerificationException
from core.dependecies import DBSession,TokenDependecy
from app.schemas.auth_schema import LoginData,Token,OtpSchema,OtpSend,PasswordReset
from core.configs import SIGN_UP_DESC,logger
from app.services.user_service import reset_password,OtpVerification,ActiveUser,GetUser
from app.services.auth import create_access_token
from app.utils.utils import verify_otp,blacklist_token,token_exp_time
from app.utils.email import create_send_otp


router = APIRouter(tags=['Auth'],prefix='/auth',)

@router.post('/signup',
             response_model=BaseUserSchema,
             status_code=status.HTTP_202_ACCEPTED,
             description=SIGN_UP_DESC)
async def signup_client(request:UserCreate):
    #NOTE - Process signup
    return await process_signup(request)

@router.post('/verify-account',response_model=Token,status_code=status.HTTP_201_CREATED)
async def verify_account(key:OtpVerification,db:DBSession):
    return await process_accnt_verification(key,db)

#NOTE - Login Route
@router.post("/login",response_model=Token)
async def login_for_access_token(form_data: PassWordRequestForm) -> Token:
    login_data = LoginData(**form_data.__dict__)
    user:UserShow = await authenticate_user(login_data)
    scopes = [user.account_type.value]
    access_token = await create_access_token(
        data={"sub": user.username,"scopes": scopes}
        )
    return Token(access_token=access_token)


@router.post('/logout',status_code=status.HTTP_202_ACCEPTED)
async def logout(current_user:GetUser,token:TokenDependecy):
    return await proccess_logout(token)



    
@router.put('/reset-password',status_code=status.HTTP_202_ACCEPTED,response_model=Token,description='Reset Password')
async def reset_pwd(current_user:ActiveUser,payload:PasswordReset,email:OtpVerification,db:DBSession):
    await reset_password(current_user,db,payload.password)
    scopes = [current_user.account_type.value]
    token = await create_access_token(data={"sub": email,"scopes": scopes})
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
        data={"sub": payload.email,"scopes": scopes},expire_time=5
        )
    return Token(access_token=access_token)
    
token_refresh_desc ='''This endpoint refreshes a user's token including the neccesary permissions for the account type,in case of <b>unauthorized</b> or <b>account type changes</b>
The previous token will be `blacklisted`'''   
@router.get('/refresh-token',response_model=Token,status_code=status.HTTP_200_OK,description=token_refresh_desc)
async def refresh_token(current_user:ActiveUser,token:TokenDependecy):
    scopes = [current_user.account_type.value]
    token_exp = await token_exp_time(token)
    await blacklist_token(token,token_exp)
    new_token = await create_access_token(data={"sub": current_user.email,"scopes": scopes})
    return Token(access_token=new_token)


    








    
    