from pydantic import Field
from enum import Enum
from typing import Annotated
from core.configs import settings

# NOTE -  Custom datatype for Phone numbers
PhoneStr = Annotated[
    str,
    Field(
        examples=[
            "+2348078417891",
        ],
        description="Phone number in international format",
        pattern=settings.PHONE_REGEX,  # type: ignore
        min_length=10,
        max_length=15,
    ),
]


class AccountTypeEnum(str, Enum):
    client = "client"
    agent = "agent"


class KycStatusEnum(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class ListingTypeEnum(str, Enum):
    rent = "rent"
    sale = "sale"


class PropertyTypeEnum(str, Enum):
    apartment = "apartment"
    land = "land"
    shortlet = "shortlet"
    shared_apartment = "shared_apartment"


class AppointmentStatEnum(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"


class WeekDayEnum(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class PropertyStatEnum(str, Enum):
    sold = "sold"
    rented = "rented"
    available = "available"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
