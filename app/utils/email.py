import smtplib
#from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from random import randint
from datetime import timedelta
 
from core.configs import redis,VERIFICATION_CODE_EXP_MIN,EMAIL,EMAIL_HOST,APP_PASS, logger,user_data_prefix,otp_prefix
from core.dependecies import env,DBSession



async def send_otp_mail(to_email,otp:str):
    template = env.get_template("otp_email.txt")
    text = template.render(otp=otp, 
                           expiry=int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60), company_name="Sheda Solution", 
                           support_email=EMAIL)
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to_email
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = '🔐 Your OTP Code for Secure Verification'
    msg.attach(MIMEText(text,))
    try:
        smtp = smtplib.SMTP(EMAIL_HOST)
        smtp.starttls()
        smtp.login(user=EMAIL,password=APP_PASS)
        smtp.sendmail(EMAIL,to_email,msg.as_string())
        logger.info('OTP Mail Sent')
        return True
    except Exception as e:
        logger.error(f'Failed to send email \n{str(e)}')
        return False
        
async def create_set_send_otp(email:str,user_data:dict) -> int:
    otp= str(randint(1000,9999))
    await redis.setex(otp_prefix.format(email),timedelta(minutes=2),otp)
    logger.info(f'otp saved to redis for {int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60)} minutes')
    await redis.hset(user_data_prefix.format(email),mapping=user_data)
    logger.info('User data set to redis')
    await redis.expire(user_data_prefix.format(email),timedelta(hours=2))
    logger.info('timer set on user data 2 hours')
    send_otp = await send_otp_mail(email,otp)
    if send_otp:
        logger.info('OTP Sent')
        return True
    logger.error('Failed to send OTP')
    return False

async def resend_otp(email:str):
    stored_otp = await redis.get(otp_prefix.format(email))
    user_data = await redis.hgetall(user_data_prefix.format(email))
    if stored_otp and user_data:
        otp = stored_otp.decode()
        send_otp = await send_otp_mail(email,otp)
        if send_otp:
            logger.info('OTP Resent')
            return True
    logger.error('OTP not found')
    otp = str(randint(1000,9999))
    await redis.setex(otp_prefix.format(email),timedelta(minutes=2),otp)
    logger.info(f'otp saved to redis for {int(VERIFICATION_CODE_EXP_MIN.total_seconds()/60)}')
    send_otp = await send_otp_mail(email,otp)
    if send_otp:
        logger.info('OTP Sent')
        return True
    
    return False

async def verify_otp(otp:str,email:str):
    stored_otp = await redis.get(otp_prefix.format(email))
    if stored_otp and stored_otp.decode() == otp:
        logger.info(f'otp verified')
        user_data = await redis.hgetall(user_data_prefix.format(email))
        user_data ={key.decode():value.decode() for key,value in user_data.items()}
        logger.info(f'{email} Data retrieved from redis')
        await redis.delete(user_data_prefix.format(email))
        logger.info(f'{email} Data deleted from redis')
        return user_data
    logger.error('OTP not found')
    return False
    
    
    
        
    






