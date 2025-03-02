from fastapi import APIRouter,status,HTTPException
from app.schemas.user_schema import BuyerCreate,UserShow,SellerCreate,BaseUserSchema
from app.services.auth import process_signup,process_accnt_verification,proccess_logout
from app.services.auth import authenticate_user,create_access_token,process_send_otp,process_fgt_pwd,verify_request_otp
from core.dependecies import PassWordRequestForm
from core.dependecies import DBSession,TokenDependecy
from app.schemas.auth_schema import LoginData,Token,OtpSchema,OtpSend,PasswordReset
from core.configs import SIGN_UP_DESC,Reset_pass_desc,logger
from app.services.user_service import get_current_user,reset_password
from app.services.auth import create_access_token
from app.utils.utils import blacklist_token,token_exp_time


router = APIRouter(tags=['Auth'],prefix='/auth',)

@router.post('/signup/buyer',
             response_model=BaseUserSchema,
             status_code=status.HTTP_202_ACCEPTED,
             description=SIGN_UP_DESC)
async def signup_buyer(request:BuyerCreate):
    #NOTE - Process signup
    return await process_signup(request)

@router.post('/signup/seller',
             response_model=BaseUserSchema,
             status_code=status.HTTP_202_ACCEPTED,
             description=SIGN_UP_DESC)
async def signup_seller(request:SellerCreate):
    
    return await process_signup(request)

#NOTE - Verification Endpoint
@router.post('/verify-accnt',response_model=Token,status_code=status.HTTP_201_CREATED)
async def verify_account(payload:OtpSchema,db:DBSession):
    
        return await process_accnt_verification(payload,db)
    
    
@router.post('/send-otp',response_model=dict,status_code=status.HTTP_202_ACCEPTED)
async def resend_otp(payload:OtpSend):
    return await process_send_otp(payload)



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
async def logout(token:TokenDependecy):
    return await proccess_logout(token)


@router.post('/fgt-pwd',status_code=status.HTTP_202_ACCEPTED,response_model=dict,description='Send OTP to email')
async def forgotten_pwd(payload:OtpSend):
    return await process_fgt_pwd(payload.email)


@router.post('/verify-otp',status_code=status.HTTP_202_ACCEPTED,response_model=Token,description=Reset_pass_desc)
async def verify_otp(payload:OtpSchema,db:DBSession,):
    verified =  await verify_request_otp(payload.email,payload.otp,db)
    if verified:
        token = await create_access_token(data={'sub':payload.email},expire_time=5)
        return Token(access_token=token)
    
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
    
    








    
    