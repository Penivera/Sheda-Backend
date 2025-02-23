import  logging
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta
import logging

load_dotenv()

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",   # Blue
        "INFO": "\033[92m",    # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "CRITICAL": "\033[1;91m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# Configure logger
logger = logging.getLogger("colored_logger")
logger.setLevel(logging.DEBUG)

# Create handler
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(levelname)s:     %(funcName)s:Line-%(lineno)d: %(message)s"))

# Add handler to logger
logger.addHandler(handler)




SIGN_UP_DESC ='''Once accounts are created they are stored temporarily for 2 hours before deletion if email verification is not completed
'''


#NOTE - Regex for Phone
PHONE_REGEX = r'^\+\d{10,15}$'


#NOTE - Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')
expire_delta = timedelta(days=30)

#NOTE - Debug mode
DEBUG_MODE = os.getenv('DEBUG_MODE')== 'True'

#NOTE -  Email Credential
EMAIL = os.getenv('EMAIL')
APP_PASS = os.getenv('APP_PASS')
EMAIL_HOST = os.getenv('EMAIL_HOST')

#NOTE - DB configs
REDIS_URL = os.getenv('REDIS_URL')
VERIFICATION_CODE_EXP_MIN = timedelta(minutes=int(os.getenv('VERIFICATION_CODE_EXP_MIN')))
DB_URL = os.getenv('DB_URL')

#NOTE -  Templates Dir
Templates_dir = os.path.join(os.getcwd(),'app','templates')

#NOTE - Application startup

    


