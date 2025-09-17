import logging
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from datetime import timedelta
import redis.asyncio as aioredis
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field,field_validator
import json


load_dotenv()


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[1;91m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


# Configure logger
logger = logging.getLogger("colored_logger")
handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter("%(levelname)s:     %(funcName)s:Line-%(lineno)d: %(message)s")
)
logger.addHandler(handler)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # General description
    SIGN_UP_DESC:str = Field(
        default="Once accounts are created they are stored temporarily for 2 hours "
        "before deletion if email verification is not completed"
    )

    # Security
    SECRET_KEY:str = Field(..., description="JWT secret key")
    ALGORITHM:str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Debug mode
    DEBUG_MODE:bool = Field(default=False, description="Debug mode flag")

    # Email settings
    EMAIL:str = Field(..., description="Email address for sending emails")
    APP_PASS:str = Field(..., description="App password for email")
    EMAIL_HOST:str = Field(default="smtp.gmail.com", description="Email host")

    # Database
    DB_URL: str = Field(..., description="Database connection URL")
    REDIS_URL: str = Field(..., description="Redis connection URL")

    # NOTE -  Host URLs
    PROD_URL: str = Field(..., description="Production Server")
    DEV_URL: str = Field(..., description="Development Server")

    # Regex
    PHONE_REGEX: str = r"^\+\d{10,15}$"

    # Verification
    VERIFICATION_CODE_EXP_MIN: int = Field(
        default=15, description="Verification code expiration in minutes"
    )

    # API
    API_V_STR: str = Field(default="/api/v1", description="API version prefix")
    
    #SECTION Cloudinary data
    
    CLOUDINARY_NAME:str = Field(...,description="Cloudinary database name")
    CLOUDINARY_API_KEY:str = Field(...,description="Cloudinary API key")
    CLOUDINARY_API_SECRET:str = Field(...,description="Cloudinary Api Key")
    CLOUDINARY_URL:str = Field(...,description="cloudinary url")

    # Redis keys
    BLACKLIST_PREFIX: str = "blacklist:{}"
    USER_DATA_PREFIX: str = "user_data:{}"
    OTP_PREFIX: str = "otp:{}"

    # Directories
    TEMPLATES_DIR: str = os.path.join(os.getcwd(), "app", "templates")
    MEDIA_DIR: str = os.path.join(os.getcwd(), "media")

    # Middleware
    ORIGINS: list[str] = Field(..., description="CORS allowed origins")
    METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods",
    )
    ALLOW_HEADERS: list[str] = Field(
        default=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        ],
        description="CORS allowed headers",
    )

    # Templates
    TEMPLATES: dict = {
        "otp": "otp_email.txt",
        "welcome": "welcome_email.txt",
        "reset_password": "reset_password.txt",
    }

    # Computed properties
    @property
    def expire_delta(self) -> timedelta:
        return timedelta(days=30)

    @property
    def verification_expire_delta(self) -> timedelta:
        return timedelta(minutes=self.VERIFICATION_CODE_EXP_MIN)

    @property
    def token_url(self):
        return f"{self.API_V_STR}/auth/login"
    



# Instantiate settings
settings = Settings()  # type: ignore

# Ensure media dir exists
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
logger.setLevel(settings.DEBUG_MODE and logging.DEBUG or logging.INFO)
logger.info(f"Settings initialized successfully with debug mode {settings.DEBUG_MODE}")
redis: aioredis.Redis = aioredis.from_url(settings.REDIS_URL)
