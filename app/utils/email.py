import smtplib
#from email.mime.application import MIMEApplication
from email_lib import render_template,EmailSender
from random import randint
from datetime import timedelta
 
from core.configs import redis,VERIFICATION_CODE_EXP_MIN,EMAIL,EMAIL_HOST,APP_PASS, logger,user_data_prefix,otp_prefix,TEMPLATES
from core.dependecies import env

token_expiration = int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60)

email_sender = EmailSender(
    smtp_host=EMAIL_HOST,
    smtp_user=EMAIL,
    smtp_pass=APP_PASS,
    from_email=EMAIL
)
        
async def create_set_send_otp(email:str,user_data:dict=None) -> int:
    otp= str(randint(1000,9999))
    await redis.setex(otp_prefix.format(email),timedelta(minutes=2),otp)
    logger.info(f'otp saved to redis for {int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60)} minutes')
    if user_data:
        await redis.hset(user_data_prefix.format(email),mapping=user_data)
        logger.info('User data set to redis')
        await redis.expire(user_data_prefix.format(email),timedelta(hours=2))
        logger.info('timer set on user data 2 hours')
    otp_text = render_template(env,TEMPLATES['otp'],otp=otp,expiry=token_expiration,support_email=EMAIL)
    send_otp = await email_sender.send_email(text=otp_text,to_email=email,subject='OTP for Verification')
                                
    if send_otp:
        logger.info('OTP Sent')
        return True
    logger.error('Failed to send OTP')
    return False

async def send_otp_for_signup(email:str):
    stored_otp = await redis.get(otp_prefix.format(email))
    user_data = await redis.hgetall(user_data_prefix.format(email))
    if stored_otp and user_data:
        otp = stored_otp.decode()
        otp_text = render_template(env,TEMPLATES['otp'],otp=otp,expiry=token_expiration,support_email=EMAIL)
        send_otp = await email_sender.send_email(text=otp_text,to_email=email,subject='OTP for Verification',)
        if send_otp:
            logger.info('OTP Resent')
            return True
    logger.error('OTP not found')
    otp = str(randint(1000,9999))
    await redis.setex(otp_prefix.format(email),timedelta(minutes=2),otp)
    logger.info(f'otp saved to redis for {int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60)}')
    otp_text = render_template(env,TEMPLATES['otp'],otp=otp,expiry=token_expiration,support_email=EMAIL)
    send_otp = await email_sender.send_email(text=otp_text,to_email=email,subject='OTP for Verification',)
    if send_otp:
        logger.info('OTP Sent')
        return True
    
    return False




    
    
    
        
    






