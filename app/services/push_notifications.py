"""
Push notification service with FCM/APNs integration.
Handles device token registration and push notification delivery.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from core.logger import get_logger
from core.exceptions import NotificationError, ExternalServiceError
from core.configs import settings

logger = get_logger(__name__)


class PushNotificationService:
    """Service for managing push notifications."""

    def __init__(self):
        """Initialize push notification service."""
        self.fcm_client = None
        self.device_tokens: Dict[int, List[str]] = {}  # user_id -> list of tokens

    async def initialize(self) -> None:
        """Initialize Firebase Cloud Messaging client."""
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            # Initialize if not already done
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FCM_CREDENTIALS)
                firebase_admin.initialize_app(cred)

            self.fcm_client = messaging
            logger.info("Firebase Cloud Messaging initialized")
        except ImportError:
            logger.warning("firebase-admin not installed, FCM disabled")
        except Exception as e:
            logger.error(f"FCM initialization failed: {str(e)}")
            raise ExternalServiceError("Firebase", "Failed to initialize FCM")

    async def register_device_token(
        self,
        user_id: int,
        device_token: str,
        device_type: str = "mobile",  # mobile, web
        device_name: Optional[str] = None,
    ) -> None:
        """
        Register device token for push notifications.

        Args:
            user_id: User ID
            device_token: FCM/APNs device token
            device_type: Device type (mobile, web)
            device_name: Optional device name/model

        Raises:
            NotificationError: If registration fails
        """
        try:
            # In production, store in database
            # For now, maintain in-memory cache
            if user_id not in self.device_tokens:
                self.device_tokens[user_id] = []

            if device_token not in self.device_tokens[user_id]:
                self.device_tokens[user_id].append(device_token)

            logger.info(
                f"Device token registered",
                user_id=user_id,
                device_type=device_type,
            )
        except Exception as e:
            logger.error(f"Device token registration failed: {str(e)}")
            raise NotificationError(detail="Failed to register device token")

    async def unregister_device_token(
        self,
        user_id: int,
        device_token: str,
    ) -> None:
        """
        Unregister device token.

        Args:
            user_id: User ID
            device_token: Device token to unregister
        """
        if user_id in self.device_tokens:
            self.device_tokens[user_id] = [
                token for token in self.device_tokens[user_id] if token != device_token
            ]

            if not self.device_tokens[user_id]:
                del self.device_tokens[user_id]

            logger.info(
                f"Device token unregistered",
                user_id=user_id,
            )

    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "general",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to user.

        Args:
            user_id: Target user ID
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Optional additional data

        Returns:
            Response with sent device count

        Raises:
            NotificationError: If sending fails
        """
        if user_id not in self.device_tokens:
            logger.warning(f"No device tokens for user {user_id}")
            return {"sent": 0, "failed": 0}

        device_tokens = self.device_tokens[user_id]
        sent_count = 0
        failed_count = 0

        for token in device_tokens:
            try:
                result = await self._send_to_device(
                    token,
                    title,
                    body,
                    notification_type,
                    data,
                )
                sent_count += 1
                logger.debug(f"Notification sent to user {user_id}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send to device {token}: {str(e)}")

        return {
            "user_id": user_id,
            "sent": sent_count,
            "failed": failed_count,
            "total": len(device_tokens),
        }

    async def send_to_multiple_users(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        notification_type: str = "general",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to multiple users.

        Args:
            user_ids: List of user IDs
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Optional additional data

        Returns:
            Aggregated response stats
        """
        total_sent = 0
        total_failed = 0

        for user_id in user_ids:
            result = await self.send_notification(
                user_id,
                title,
                body,
                notification_type,
                data,
            )
            total_sent += result["sent"]
            total_failed += result["failed"]

        return {
            "users": len(user_ids),
            "total_sent": total_sent,
            "total_failed": total_failed,
        }

    async def _send_to_device(
        self,
        device_token: str,
        title: str,
        body: str,
        notification_type: str,
        data: Optional[Dict[str, Any]],
    ) -> str:
        """
        Send notification to specific device.

        Args:
            device_token: Device token
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Additional data

        Returns:
            FCM message ID

        Raises:
            Exception: If sending fails
        """
        if not self.fcm_client:
            logger.warning("FCM not initialized, skipping notification")
            return "mock_message_id"

        from firebase_admin import messaging

        # Build message
        message_data = data or {}
        message_data["notification_type"] = notification_type

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=message_data,
            tokens=[device_token],
        )

        try:
            response = self.fcm_client.send_multicast(message)
            if response.failure_count > 0:
                raise Exception(f"FCM sent {response.failure_count} failed")
            return response.responses[0].message_id
        except Exception as e:
            raise Exception(f"FCM send failed: {str(e)}")


class NotificationTemplates:
    """Pre-defined notification templates."""

    @staticmethod
    def bid_placed(
        property_title: str,
        bid_amount: float,
        bidder_name: str,
    ) -> tuple[str, str]:
        """Bid placed notification."""
        title = "New Bid Received"
        body = f"{bidder_name} placed a bid of {bid_amount} on {property_title}"
        return title, body

    @staticmethod
    def bid_accepted(
        property_title: str,
    ) -> tuple[str, str]:
        """Bid accepted notification."""
        title = "Bid Accepted"
        body = f"Your bid for {property_title} has been accepted"
        return title, body

    @staticmethod
    def payment_received(
        amount: float,
        property_title: str,
    ) -> tuple[str, str]:
        """Payment received notification."""
        title = "Payment Received"
        body = f"Payment of {amount} received for {property_title}"
        return title, body

    @staticmethod
    def contract_signed(
        property_title: str,
    ) -> tuple[str, str]:
        """Contract signed notification."""
        title = "Contract Signed"
        body = f"Contract for {property_title} has been successfully signed"
        return title, body

    @staticmethod
    def message_received(
        sender_name: str,
    ) -> tuple[str, str]:
        """New message notification."""
        title = "New Message"
        body = f"{sender_name} sent you a message"
        return title, body

    @staticmethod
    def appointment_reminder(
        property_title: str,
        time: str,
    ) -> tuple[str, str]:
        """Appointment reminder."""
        title = "Appointment Reminder"
        body = f"Don't forget your appointment for {property_title} at {time}"
        return title, body

    @staticmethod
    def kyc_approved() -> tuple[str, str]:
        """KYC approved notification."""
        title = "KYC Approved"
        body = "Your identity has been verified successfully"
        return title, body

    @staticmethod
    def kyc_rejected(reason: str = "document quality") -> tuple[str, str]:
        """KYC rejected notification."""
        title = "KYC Rejected"
        body = f"Your KYC was rejected due to {reason}. Please try again."
        return title, body


# Global service instance
_notification_service: Optional[PushNotificationService] = None


async def get_notification_service() -> PushNotificationService:
    """
    Get or create global notification service.

    Returns:
        PushNotificationService instance
    """
    global _notification_service

    if _notification_service is None:
        _notification_service = PushNotificationService()
        try:
            await _notification_service.initialize()
        except Exception as e:
            logger.warning(f"FCM initialization failed, notifications disabled: {e}")

    return _notification_service
