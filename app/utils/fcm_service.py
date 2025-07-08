"""
Firebase Cloud Messaging (FCM) service for push notifications.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging service for sending push notifications."""

    def __init__(self):
        self.server_key = settings.firebase_server_key
        self.project_id = settings.firebase_project_id
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.fcm_v1_url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"

    def _get_headers(self, use_v1: bool = False) -> Dict[str, str]:
        """Get headers for FCM request."""
        if use_v1:
            # For FCM v1 API (requires OAuth 2.0)
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_access_token()}"
            }
        else:
            # For legacy FCM API
            return {
                "Content-Type": "application/json",
                "Authorization": f"key={self.server_key}"
            }

    def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token for FCM v1 API."""
        # In a real implementation, you would use Google's OAuth 2.0 library
        # For now, we'll use the legacy API
        return ""

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "message",
        priority: str = "high"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Send a push notification to a single device.
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            notification_type: Type of notification
            priority: Notification priority (high/normal)
            
        Returns:
            Tuple of (success, message_id, error_message)
        """
        try:
            payload = {
                "to": token,
                "priority": priority,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default",
                    "badge": 1
                }
            }
            
            # Add data payload if provided
            if data:
                payload["data"] = {
                    "notification_type": notification_type,
                    **{k: str(v) if not isinstance(v, str) else v for k, v in data.items()}
                }
            
            # Add platform-specific configurations
            payload["android"] = {
                "priority": priority,
                "notification": {
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    "channel_id": "default_channel"
                }
            }
            
            payload["apns"] = {
                "headers": {
                    "apns-priority": "10" if priority == "high" else "5"
                },
                "payload": {
                    "aps": {
                        "alert": {
                            "title": title,
                            "body": body
                        },
                        "sound": "default",
                        "badge": 1,
                        "category": notification_type
                    }
                }
            }
            
            headers = self._get_headers(use_v1=False)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", 0) > 0:
                        message_id = result.get("results", [{}])[0].get("message_id")
                        logger.info(f"FCM notification sent successfully: {message_id}")
                        return True, message_id, None
                    else:
                        error = result.get("results", [{}])[0].get("error", "Unknown error")
                        logger.error(f"FCM notification failed: {error}")
                        return False, None, error
                else:
                    error_msg = f"FCM request failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg
                    
        except Exception as e:
            error_msg = f"Error sending FCM notification: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    async def send_multicast_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "message",
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a push notification to multiple devices.
        
        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            notification_type: Type of notification
            priority: Notification priority
            
        Returns:
            Dictionary with success count, failure count, and results
        """
        try:
            if not tokens:
                return {"success_count": 0, "failure_count": 0, "results": []}
            
            # Split tokens into batches of 1000 (FCM limit)
            batch_size = 1000
            all_results = []
            total_success = 0
            total_failure = 0
            
            for i in range(0, len(tokens), batch_size):
                batch_tokens = tokens[i:i + batch_size]
                
                payload = {
                    "registration_ids": batch_tokens,
                    "priority": priority,
                    "notification": {
                        "title": title,
                        "body": body,
                        "sound": "default",
                        "badge": 1
                    }
                }
                
                if data:
                    payload["data"] = {
                        "notification_type": notification_type,
                        **{k: str(v) if not isinstance(v, str) else v for k, v in data.items()}
                    }
                
                # Add platform-specific configurations
                payload["android"] = {
                    "priority": priority,
                    "notification": {
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                        "channel_id": "default_channel"
                    }
                }
                
                payload["apns"] = {
                    "headers": {
                        "apns-priority": "10" if priority == "high" else "5"
                    },
                    "payload": {
                        "aps": {
                            "alert": {
                                "title": title,
                                "body": body
                            },
                            "sound": "default",
                            "badge": 1,
                            "category": notification_type
                        }
                    }
                }
                
                headers = self._get_headers(use_v1=False)
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.fcm_url,
                        headers=headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        batch_success = result.get("success", 0)
                        batch_failure = result.get("failure", 0)
                        
                        total_success += batch_success
                        total_failure += batch_failure
                        
                        all_results.extend(result.get("results", []))
                        
                        logger.info(f"FCM batch sent: {batch_success} success, {batch_failure} failures")
                    else:
                        error_msg = f"FCM batch failed: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        total_failure += len(batch_tokens)
                        all_results.extend([{"error": error_msg}] * len(batch_tokens))
            
            return {
                "success_count": total_success,
                "failure_count": total_failure,
                "results": all_results
            }
            
        except Exception as e:
            error_msg = f"Error sending FCM multicast: {str(e)}"
            logger.error(error_msg)
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "results": [{"error": error_msg}] * len(tokens)
            }

    async def send_topic_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "system",
        priority: str = "normal"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send a notification to a topic (broadcast).
        
        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Additional data payload
            notification_type: Type of notification
            priority: Notification priority
            
        Returns:
            Tuple of (success, message_id, error_message)
        """
        try:
            payload = {
                "to": f"/topics/{topic}",
                "priority": priority,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default"
                }
            }
            
            if data:
                payload["data"] = {
                    "notification_type": notification_type,
                    **{k: str(v) if not isinstance(v, str) else v for k, v in data.items()}
                }
            
            headers = self._get_headers(use_v1=False)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get("message_id")
                    logger.info(f"FCM topic notification sent: {message_id}")
                    return True, message_id, None
                else:
                    error_msg = f"FCM topic notification failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg
                    
        except Exception as e:
            error_msg = f"Error sending FCM topic notification: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def validate_token(self, token: str) -> bool:
        """
        Validate if an FCM token is in the correct format.
        
        Args:
            token: FCM device token
            
        Returns:
            True if token format is valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False
        
        # Basic FCM token validation (tokens are typically 152+ characters)
        if len(token) < 140:
            return False
        
        # FCM tokens are base64-like strings
        import re
        token_pattern = r'^[A-Za-z0-9_-]+$'
        return bool(re.match(token_pattern, token.replace(':', '').replace('-', '')))


# Global FCM service instance
fcm_service = FCMService()
