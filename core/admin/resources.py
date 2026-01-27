from app.models import *
from starlette_admin.contrib.sqla import ModelView
from starlette_admin import DateField, ImageField, PasswordField, EnumField
from starlette.requests import Request
from starlette.datastructures import UploadFile
from typing import Any, Dict
from app.utils.utils import hash_password
import cloudinary.uploader
from app.utils.enums import AccountTypeEnum, KycStatusEnum, UserRole
from starlette_admin.exceptions import FormValidationError
from starlette.templating import Jinja2Templates
from starlette_admin.views import CustomView
from starlette.responses import HTMLResponse




class BaseUserModelView(ModelView):
    icon = "fa fa-user"

    # Configure fields: ImageField shows upload button, PasswordField masks input
    fields = [
        "id",
        "username",
        "email",
        ImageField("avatar_url", required=False),
        PasswordField("password"),
        "fullname",
        "phone_number",
        "location",
        EnumField("account_type", enum=AccountTypeEnum),
        EnumField("kyc_status", enum=KycStatusEnum),
        EnumField("role", enum=UserRole),
        "is_active",
        "verified",
        "created_at",
        "updated_at",
    ]

    # Don't show password hash in list/detail
    exclude_fields_from_list = ["password"]
    exclude_fields_from_detail = ["password"]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self._handle_password_and_avatar(data)
        if "avatar_url" in data:
            obj.avatar_url = data["avatar_url"]
        if "password" in data:
            obj.password = data["password"]

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self._handle_password_and_avatar(data, is_edit=True)
        if "avatar_url" in data:
            obj.avatar_url = data["avatar_url"]
        if "password" in data:
            obj.password = data["password"]

    async def _handle_password_and_avatar(
        self, data: Dict[str, Any], is_edit: bool = False
    ):
        # 1. Handle Password Hashing
        password = data.get("password")
        if password:
            data["password"] = hash_password(password)
        elif is_edit:
            # If editing and password is empty, remove key to keep existing password
            data.pop("password", None)

        # 2. Handle Avatar Upload to Cloudinary
        avatar = data.get("avatar_url")

        # Starlette Admin stores ImageField as (UploadFile, bool)
        if isinstance(avatar, tuple):
            avatar_file = avatar[0]  # extract UploadFile
        else:
            avatar_file = avatar

        if isinstance(avatar_file, UploadFile):
            try:
                content = await avatar_file.read()
                if content:
                    # Upload to Cloudinary
                    response = cloudinary.uploader.upload(
                        content, folder="profile_pictures"
                    )
                    # Replace the tuple/file with the string URL
                    data["avatar_url"] = response.get("secure_url")
                else:
                    data.pop("avatar_url", None)
            except Exception as e:
                print(f"Error uploading avatar: {e}")
                data.pop("avatar_url", None)
        else:
            # If it's not a file (e.g. existing URL string or None)
            if is_edit and not avatar_file:
                data.pop("avatar_url", None)


class ClientModelView(BaseUserModelView):
    """
    Admin model for managing clients.
    MUST inherit from BaseUserModelView to use the upload logic.
    """

    icon = "fa fa-user"

    exclude_fields_from_list = ["properties", "password"]
    exclude_fields_from_detail = ["properties", "password"]


class AgentModelView(BaseUserModelView):
    """
    Admin model for managing agents.
    IMPORTANT: Inherits from BaseUserModelView to get password hashing and image upload logic.
    """

    icon = "fa fa-user-tie"

    # Exclude properties to prevent 'eager loading' errors
    exclude_fields_from_list = [
        "listings",
        "availabilities",
        "appointments",
        "password",
    ]
    exclude_fields_from_detail = [
        "listings",
        "availabilities",
        "appointments",
        "password",
    ]


class PropertyModelView(ModelView):
    icon = "fa fa-building"

    label = "Properties"
    name = "Property"


class PropertyImageModelView(ModelView):
    """Handles Property Image uploads."""

    icon = "fa fa-image"

    fields = [
        "id",
        "property",  # Relationship field
        ImageField("image_url"),  # File upload field
        "is_primary",
    ]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self._handle_image_upload(data)

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self._handle_image_upload(data, is_edit=True)
        if "image_url" in data:
            obj.image_url = data["image_url"]

    async def _handle_image_upload(self, data: Dict[str, Any], is_edit: bool = False):
        image = data.get("image_url")

        if isinstance(image, tuple):
            image_file = image[0]  # extract UploadFile
        else:
            image_file = image

        if isinstance(image_file, UploadFile):
            response = cloudinary.uploader.upload(
                image_file.read(), folder="profile_pictures"
            )
            url = response.get("secure_url")
            if url:
                data["image_url"] = url
            else:
                # If upload failed or was empty, remove key to avoid DB error
                data.pop("image_url", None)
        elif not data.get("image_url") and is_edit:
            data.pop("image_url", None)


class ContractModelView(ModelView):
    """Handles Contracts with Date Validation."""

    icon = "fa fa-file-contract"

    fields = [
        "id",
        "property",
        "client_id",
        "agent_id",
        "contract_type",
        "amount",
        DateField("start_date"),
        DateField("end_date"),
        "is_active",
        "property",
        "payment_confirmation",
    ]

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        """Validate that end_date is after start_date."""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date:
            if end_date < start_date:
                # This raises a validation error in the Admin UI
                raise FormValidationError(
                    {"end_date": "End date cannot be before start date."}
                )

        return await super().validate(request, data)
