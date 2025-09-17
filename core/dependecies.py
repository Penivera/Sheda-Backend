from fastapi import Depends, Form, HTTPException, status
from core.database import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from jinja2 import Environment, FileSystemLoader
from fastapi.security import OAuth2PasswordBearer
from app.utils.enums import AccountTypeEnum
from core.configs import settings

env = Environment(loader=FileSystemLoader("app/templates"))


class CustomOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        username: str = Form(description="Enter Phone,email,username", default="Admin"),
        password: str = Form(description="Enter Your Password", default="admin"),
    ):
        super().__init__(username=username, password=password)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.token_url,
    scopes={
        AccountTypeEnum.agent.value: "Allow creating and managing products",
        AccountTypeEnum.client.value: "Allow view and purchase of products",
        "otp": "Temporary access for OTP verification",
        "admin": "Admin access to all endpoints",
    },
)
TokenDependecy = Annotated[str, Depends(oauth2_scheme)]

DBSession = Annotated[AsyncSession, Depends(get_db)]
PassWordRequestForm = Annotated[CustomOAuth2PasswordRequestForm, Depends()]


InvalidCredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)


VerificationException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP Or Expired Token"
)

FileUploadException = HTTPException(status_code=400, detail="No file uploaded")
