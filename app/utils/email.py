# from email.mime.application import MIMEApplication
from email_lib import render_template, EmailSender
from random import randint

from core.configs import settings, logger, redis
from core.dependecies import env


email_sender = EmailSender(
    smtp_host=settings.EMAIL_HOST,
    smtp_user=settings.EMAIL,
    smtp_pass=settings.APP_PASS,
    from_email=settings.EMAIL,
)  # type: ignore


async def create_send_otp(email: str, length: int = 4) -> int:
    otp = "".join(str(randint(0, 9)) for _ in range(length))
    await redis.setex(settings.OTP_PREFIX.format(email), 300, otp)
    logger.info(f"otp saved to redis for {settings.verification_expire_delta} minutes")
    otp_text = render_template(
        env,
        settings.TEMPLATES["otp"],
        otp=otp,
        expiry=settings.verification_expire_delta,
        support_email=settings.EMAIL,
    )
    send_otp = await email_sender.send_email(
        text=otp_text, to_email=email, subject="OTP for Verification"
    )
    if settings.DEBUG_MODE:
        logger.info(f"OTP: {otp}")

    if send_otp:
        logger.info("OTP Sent")
        return True
    logger.error("Failed to send OTP")
    return False
