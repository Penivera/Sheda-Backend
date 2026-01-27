# Models package for the project
# Re-export all model classes for easier imports
from .user import BaseUser, Client, Agent, Admin
from .property import (
    Property,
    PropertyImage,
    Appointment,
    AgentAvailability,
    Contract,
    AccountInfo,
    PaymentConfirmation,
)
from .chat import ChatMessage

__all__ = [
    "BaseUser",
    "Client",
    "Agent",
    "Admin",
    "Property",
    "PropertyImage",
    "Appointment",
    "AgentAvailability",
    "Contract",
    "AccountInfo",
    "PaymentConfirmation",
    "ChatMessage",
]
