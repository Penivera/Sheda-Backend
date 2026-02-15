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
        max_length=15,
    ),
]


class AccountTypeEnum(str, Enum):
    client = "client"
    agent = "agent"
    admin = "admin"

    @staticmethod
    def to_list() -> list:
        return [e.value for e in AccountTypeEnum]


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
    available = "available"
    sold = "sold"
    rented = "rented"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class TransactionStatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"
    docs_released = "docs_released"
    docs_confirmed = "docs_confirmed"
    payment_released = "payment_released"
    completed = "completed"
    disputed = "disputed"


class TransactionEventEnum(str, Enum):
    bid_accepted = "bid_accepted"
    bid_rejected = "bid_rejected"
    docs_released = "docs_released"
    docs_confirmed = "docs_confirmed"
    payment_released = "payment_released"


class TransactionActionEnum(str, Enum):
    purchase = "purchase"
    lease = "lease"
