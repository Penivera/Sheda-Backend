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
    bid_placed = "bid_placed"
    bid_accepted = "bid_accepted"
    bid_rejected = "bid_rejected"
    bid_cancelled = "bid_cancelled"
    docs_released = "docs_released"
    docs_confirmed = "docs_confirmed"
    payment_released = "payment_released"
    transaction_completed = "transaction_completed"
    dispute_raised = "dispute_raised"
    # Appointment sub-flow — no on-chain BidStatus equivalent, so these don't
    # appear in EVENT_STATUS_MAP (services/transactions.py) and don't change
    # TransactionRecord.status; they're persisted in metadata_payload instead
    # (see upsert_transaction_from_event's is_appointment_event branch).
    appointment_booked = "appointment_booked"
    appointment_accepted = "appointment_accepted"
    appointment_rejected = "appointment_rejected"


class TransactionActionEnum(str, Enum):
    purchase = "purchase"
    lease = "lease"
