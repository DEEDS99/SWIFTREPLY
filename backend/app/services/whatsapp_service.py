"""
SwiftReply — Meta WhatsApp Business Cloud API Service
======================================================
Handles sending messages, downloading media, and webhook verification.
"""

import os
import hashlib
import hmac
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("swiftreply.whatsapp")

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v19.0")


class WhatsAppService:
    """Meta WhatsApp Business Cloud API client."""

    def __init__(self, token: Optional[str] = None, phone_id: Optional[str] = None):
        self.token = token or os.getenv("WHATSAPP_TOKEN")
        self.phone_id = phone_id or os.getenv("WHATSAPP_PHONE_ID")
        self.base_url = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}"

    def _headers(self, token: Optional[str] = None) -> dict:
        return {
            "Authorization": f"Bearer {token or self.token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        text: str,
        reply_to_id: Optional[str] = None,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        """Send a plain text message."""
        pid = phone_id or self.phone_id
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        if reply_to_id:
            payload["context"] = {"message_id": reply_to_id}

        return await self._post(f"/messages", payload, token=token, phone_id=pid)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[list] = None,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        """Send a pre-approved WhatsApp template message."""
        pid = phone_id or self.phone_id
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }
        return await self._post("/messages", payload, token=token, phone_id=pid)

    async def send_image_message(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        """Send an image message."""
        pid = phone_id or self.phone_id
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption or ""},
        }
        return await self._post("/messages", payload, token=token, phone_id=pid)

    async def send_document_message(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        """Send a document/file message."""
        pid = phone_id or self.phone_id
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": document_url, "filename": filename, "caption": caption or ""},
        }
        return await self._post("/messages", payload, token=token, phone_id=pid)

    async def mark_message_read(
        self,
        message_id: str,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        """Mark an incoming message as read."""
        pid = phone_id or self.phone_id
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post("/messages", payload, token=token, phone_id=pid)

    async def download_media(
        self,
        media_id: str,
        token: Optional[str] = None,
    ) -> Optional[bytes]:
        """Download media file from Meta servers."""
        t = token or self.token
        # Step 1: Get media URL
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/{media_id}",
                headers={"Authorization": f"Bearer {t}"},
            )
            if r.status_code != 200:
                logger.error(f"Failed to get media URL: {r.text}")
                return None
            media_url = r.json().get("url")

        # Step 2: Download from URL
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(media_url, headers={"Authorization": f"Bearer {t}"})
            if r.status_code == 200:
                return r.content
        return None

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Meta webhook X-Hub-Signature-256 header."""
        app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
        if not app_secret:
            return True  # Skip in dev if not configured
        expected = hmac.new(
            app_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    async def _post(
        self,
        path: str,
        payload: dict,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ) -> dict:
        pid = phone_id or self.phone_id
        url = f"{self.base_url}/{pid}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.post(url, json=payload, headers=self._headers(token))
                result = r.json()
                if r.status_code not in (200, 201):
                    logger.error(f"WhatsApp API error {r.status_code}: {result}")
                return result
            except Exception as e:
                logger.error(f"WhatsApp send error: {e}")
                return {"error": str(e)}


# Singleton
whatsapp_service = WhatsAppService()
