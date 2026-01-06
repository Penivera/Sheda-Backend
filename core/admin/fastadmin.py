from __future__ import annotations

from fastadmin import SqlAlchemyModelAdmin, register

from core.database import AsyncSessionLocal

from app.models.chat import ChatMessage
from app.models.user import BaseUser, Client, Agent
from app.models.property import (
    Property,
    PropertyImage,
    Appointment,
    Contract,
    PaymentConfirmation,
    AgentAvailability,
    AccountInfo,
)


# =============================================================================
# User Models
# =============================================================================


@register(BaseUser, sqlalchemy_sessionmaker=AsyncSessionLocal)
class BaseUserAdmin(SqlAlchemyModelAdmin):
    """Admin for all users (polymorphic base)."""

    icon = "fa fa-users"
    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "account_type",
        "fullname",
        "location",
        "role",
        "kyc_status",
        "is_active",
        "verified",
        "is_deleted",
        "last_seen",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "username", "email")
    search_fields = ("id", "username", "email", "phone_number", "fullname", "location")
    list_filter = (
        "account_type",
        "role",
        "kyc_status",
        "is_active",
        "verified",
        "is_deleted",
    )
    ordering = ("-created_at",)
    # Hide password from display but allow editing
    exclude = ("password",)


@register(Client, sqlalchemy_sessionmaker=AsyncSessionLocal)
class ClientAdmin(SqlAlchemyModelAdmin):
    """Admin for Client users."""

    icon = "fa fa-user"
    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "fullname",
        "location",
        "role",
        "kyc_status",
        "is_active",
        "verified",
        "is_deleted",
        "last_seen",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "username", "email")
    search_fields = ("id", "username", "email", "phone_number", "fullname", "location")
    list_filter = ("role", "kyc_status", "is_active", "verified", "is_deleted")
    ordering = ("-created_at",)
    exclude = ("password",)


@register(Agent, sqlalchemy_sessionmaker=AsyncSessionLocal)
class AgentAdmin(SqlAlchemyModelAdmin):
    """Admin for Agent users."""

    icon = "fa fa-user-tie"
    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "fullname",
        "agency_name",
        "rating",
        "location",
        "role",
        "kyc_status",
        "is_active",
        "verified",
        "is_deleted",
        "last_seen",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "username", "email")
    search_fields = (
        "id",
        "username",
        "email",
        "phone_number",
        "fullname",
        "agency_name",
        "location",
    )
    list_filter = ("role", "kyc_status", "is_active", "verified", "is_deleted")
    ordering = ("-created_at",)
    exclude = ("password",)


# =============================================================================
# Property Models
# =============================================================================


@register(Property, sqlalchemy_sessionmaker=AsyncSessionLocal)
class PropertyAdmin(SqlAlchemyModelAdmin):
    """Admin for Property listings."""

    icon = "fa fa-home"
    list_display = (
        "id",
        "title",
        "price",
        "is_negotiable",
        "location",
        "property_type",
        "listing_type",
        "status",
        "furnished",
        "is_active",
        "bedroom",
        "bathroom",
        "air_condition",
        "pop_ceiling",
        "floor_tiles",
        "running_water",
        "furniture",
        "prepaid_meter",
        "wifi",
        "agent_id",
        "client_id",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "title")
    search_fields = ("id", "title", "description", "location")
    list_filter = (
        "status",
        "property_type",
        "listing_type",
        "furnished",
        "is_active",
        "is_negotiable",
        "air_condition",
        "wifi",
    )
    ordering = ("-created_at",)


@register(PropertyImage, sqlalchemy_sessionmaker=AsyncSessionLocal)
class PropertyImageAdmin(SqlAlchemyModelAdmin):
    """Admin for Property images."""

    icon = "fa fa-image"
    list_display = ("id", "property_id", "image_url", "is_primary")
    list_display_links = ("id",)
    search_fields = ("id", "property_id", "image_url")
    list_filter = ("is_primary",)


@register(Appointment, sqlalchemy_sessionmaker=AsyncSessionLocal)
class AppointmentAdmin(SqlAlchemyModelAdmin):
    """Admin for Appointments."""

    icon = "fa fa-calendar"
    list_display = (
        "id",
        "property_id",
        "client_id",
        "agent_id",
        "scheduled_at",
        "status",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id",)
    search_fields = ("id", "property_id", "client_id", "agent_id")
    list_filter = ("status",)
    ordering = ("-scheduled_at",)


@register(Contract, sqlalchemy_sessionmaker=AsyncSessionLocal)
class ContractAdmin(SqlAlchemyModelAdmin):
    """Admin for Contracts."""

    icon = "fa fa-file-contract"
    list_display = (
        "id",
        "property_id",
        "client_id",
        "agent_id",
        "contract_type",
        "amount",
        "start_date",
        "end_date",
        "is_active",
    )
    list_display_links = ("id",)
    search_fields = ("id", "property_id", "client_id", "agent_id")
    list_filter = ("contract_type", "is_active")
    ordering = ("-start_date",)


@register(PaymentConfirmation, sqlalchemy_sessionmaker=AsyncSessionLocal)
class PaymentConfirmationAdmin(SqlAlchemyModelAdmin):
    """Admin for Payment confirmations."""

    icon = "fa fa-money-check"
    list_display = (
        "id",
        "contract_id",
        "client_id",
        "agent_id",
        "is_confirmed",
        "created_at",
    )
    list_display_links = ("id",)
    search_fields = ("id", "contract_id", "client_id", "agent_id")
    list_filter = ("is_confirmed",)
    ordering = ("-created_at",)


@register(AgentAvailability, sqlalchemy_sessionmaker=AsyncSessionLocal)
class AgentAvailabilityAdmin(SqlAlchemyModelAdmin):
    """Admin for Agent availability slots."""

    icon = "fa fa-clock"
    list_display = ("id", "agent_id", "weekday", "start_time", "end_time", "is_booked")
    list_display_links = ("id",)
    search_fields = ("id", "agent_id")
    list_filter = ("weekday", "is_booked")


@register(AccountInfo, sqlalchemy_sessionmaker=AsyncSessionLocal)
class AccountInfoAdmin(SqlAlchemyModelAdmin):
    """Admin for Bank account information."""

    icon = "fa fa-university"
    list_display = ("id", "user_id", "bank_name", "account_name", "account_number")
    list_display_links = ("id",)
    search_fields = ("id", "user_id", "account_number", "account_name", "bank_name")
    list_filter = ("bank_name",)


# =============================================================================
# Chat Models
# =============================================================================


@register(ChatMessage, sqlalchemy_sessionmaker=AsyncSessionLocal)
class ChatMessageAdmin(SqlAlchemyModelAdmin):
    """Admin for Chat messages."""

    icon = "fa fa-comments"
    list_display = (
        "id",
        "sender_id",
        "receiver_id",
        "property_id",
        "message",
        "is_read",
        "timestamp",
    )
    list_display_links = ("id",)
    search_fields = ("id", "sender_id", "receiver_id", "property_id", "message")
    list_filter = ("is_read",)
    ordering = ("-timestamp",)
