"""
SwiftReply — Evolution API v2 Service
=======================================
Evolution API is a self-hosted WhatsApp REST API that connects via
the WhatsApp Web protocol — 100% ToS-compliant as it acts as a
WhatsApp Web client, not the Business API. It provides:

  - REST endpoints for sending all message types
  - Webhook callbacks for receiving messages
  - QR code pairing (no Meta Business verification needed)
  - Full multimodal: text, image, audio, video, document, sticker

Docs: https://doc.evolution-api.com
GitHub: https://github.com/EvolutionAPI/evolution-api
"""

import os
import base64
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("swiftreply.evolution")


class EvolutionService:
    """
    Client for Evolution API v2 REST endpoints.
    One instance per Evolution API deployment.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instance: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("EVOLUTION_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("EVOLUTION_API_KEY", "")
        self.instance = instance or os.getenv("EVOLUTION_INSTANCE", "swiftreply")

    def _headers(self, key: Optional[str] = None) -> dict:
        return {
            "apikey": key or self.api_key,
            "Content-Type": "application/json",
        }

    # ─── Instance Management ──────────────────────────────────────────

    async def create_instance(self, instance_name: str, webhook_url: str) -> dict:
        """Create a new Evolution API instance and set its webhook."""
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.base_url}/instance/create",
                headers=self._headers(),
                json={
                    "instanceName": instance_name,
                    "qrcode": True,
                    "webhook": webhook_url,
                    "webhook_by_events": False,
                    "events": [
                        "MESSAGES_UPSERT",
                        "MESSAGES_UPDATE",
                        "CONNECTION_UPDATE",
                        "QRCODE_UPDATED",
                    ],
                },
            )
            return r.json()

    async def get_instance_info(self, instance: Optional[str] = None) -> dict:
        """Get connection status and info for an instance."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/instance/fetchInstances",
                headers=self._headers(),
                params={"instanceName": inst},
            )
            return r.json()

    async def get_qr_code(self, instance: Optional[str] = None) -> dict:
        """Get QR code for pairing this instance with WhatsApp."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/instance/connect/{inst}",
                headers=self._headers(),
            )
            return r.json()

    async def get_connection_state(self, instance: Optional[str] = None) -> dict:
        """Get current connection state: open | close | connecting."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{self.base_url}/instance/connectionState/{inst}",
                headers=self._headers(),
            )
            return r.json()

    async def logout_instance(self, instance: Optional[str] = None) -> dict:
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.delete(
                f"{self.base_url}/instance/logout/{inst}",
                headers=self._headers(),
            )
            return r.json()

    async def set_webhook(self, webhook_url: str, instance: Optional[str] = None) -> dict:
        """Configure the webhook URL for an instance."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{self.base_url}/webhook/set/{inst}",
                headers=self._headers(),
                json={
                    "url": webhook_url,
                    "webhook_by_events": False,
                    "webhook_base64": False,
                    "events": [
                        "MESSAGES_UPSERT",
                        "MESSAGES_UPDATE",
                        "CONNECTION_UPDATE",
                    ],
                },
            )
            return r.json()

    # ─── Sending Messages ─────────────────────────────────────────────

    async def send_text(
        self,
        to: str,
        text: str,
        reply_to: Optional[str] = None,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Send a plain text message."""
        inst = instance or self.instance
        payload = {
            "number": self._normalize_number(to),
            "text": text,
        }
        if reply_to:
            payload["quoted"] = {"key": {"id": reply_to}}
        return await self._post(f"/message/sendText/{inst}", payload, api_key=api_key)

    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Send an image from URL."""
        inst = instance or self.instance
        return await self._post(f"/message/sendMedia/{inst}", {
            "number": self._normalize_number(to),
            "mediatype": "image",
            "media": image_url,
            "caption": caption or "",
        }, api_key=api_key)

    async def send_audio(
        self,
        to: str,
        audio_url: str,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Send audio/voice note."""
        inst = instance or self.instance
        return await self._post(f"/message/sendWhatsAppAudio/{inst}", {
            "number": self._normalize_number(to),
            "audio": audio_url,
            "encoding": True,
        }, api_key=api_key)

    async def send_video(
        self,
        to: str,
        video_url: str,
        caption: Optional[str] = None,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Send a video."""
        inst = instance or self.instance
        return await self._post(f"/message/sendMedia/{inst}", {
            "number": self._normalize_number(to),
            "mediatype": "video",
            "media": video_url,
            "caption": caption or "",
        }, api_key=api_key)

    async def send_document(
        self,
        to: str,
        doc_url: str,
        filename: str,
        caption: Optional[str] = None,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Send a document/file."""
        inst = instance or self.instance
        return await self._post(f"/message/sendMedia/{inst}", {
            "number": self._normalize_number(to),
            "mediatype": "document",
            "media": doc_url,
            "fileName": filename,
            "caption": caption or "",
        }, api_key=api_key)

    async def send_template_text(
        self,
        to: str,
        template_body: str,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """
        Evolution API uses sendText for all outbound — no Meta template approval needed.
        Templates are just pre-written text managed in our DB.
        """
        return await self.send_text(to, template_body, instance=instance, api_key=api_key)

    async def mark_message_read(
        self,
        message_id: str,
        remote_jid: str,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Mark a message as read."""
        inst = instance or self.instance
        return await self._post(f"/message/markMessageAsRead/{inst}", {
            "read_messages": [{"id": message_id, "fromMe": False, "remoteJid": remote_jid}]
        }, api_key=api_key)

    async def get_contacts(self, instance: Optional[str] = None) -> list:
        """Fetch all contacts from WhatsApp."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/chat/findContacts/{inst}",
                headers=self._headers(),
            )
            data = r.json()
            return data if isinstance(data, list) else []

    async def get_chats(self, instance: Optional[str] = None) -> list:
        """Fetch all chats."""
        inst = instance or self.instance
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/chat/findChats/{inst}",
                headers=self._headers(),
            )
            data = r.json()
            return data if isinstance(data, list) else []

    async def download_media_base64(
        self,
        message: dict,
        instance: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Optional[dict]:
        """Download media from an incoming message as base64."""
        inst = instance or self.instance
        result = await self._post(f"/chat/getBase64FromMediaMessage/{inst}", {
            "message": message,
            "convertToMp4": False,
        }, api_key=api_key)
        return result

    # ─── Helpers ──────────────────────────────────────────────────────

    def _normalize_number(self, number: str) -> str:
        """Normalize phone number for Evolution API (strip + prefix)."""
        clean = number.replace("+", "").replace(" ", "").replace("-", "")
        return clean

    async def _post(self, path: str, payload: dict, api_key: Optional[str] = None) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.post(url, json=payload, headers=self._headers(api_key))
                return r.json()
            except Exception as e:
                logger.error(f"Evolution API error [{path}]: {e}")
                return {"error": str(e)}


# ─── Parse incoming Evolution webhook payload ─────────────────────

def parse_evolution_webhook(body: dict) -> Optional[dict]:
    """
    Parse an incoming Evolution API webhook event.

    Evolution sends:
    {
      "event": "messages.upsert",
      "instance": "my-instance",
      "data": {
        "key": { "id": "...", "remoteJid": "2607...@s.whatsapp.net", "fromMe": false },
        "message": { "conversation": "Hello" },
        "messageType": "conversation",
        "messageTimestamp": 1700000000,
        "pushName": "John Banda",
        ...
      }
    }
    """
    event = body.get("event", "")
    instance = body.get("instance", "")

    if event == "messages.upsert":
        data = body.get("data", {})
        key = data.get("key", {})

        # Skip messages sent by us
        if key.get("fromMe"):
            return None

        remote_jid = key.get("remoteJid", "")
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
        contact_name = data.get("pushName", phone)
        msg_id = key.get("id", "")
        msg_type_raw = data.get("messageType", "conversation")
        message = data.get("message", {})

        # Map Evolution message types to our types
        type_map = {
            "conversation": "text",
            "extendedTextMessage": "text",
            "imageMessage": "image",
            "audioMessage": "audio",
            "videoMessage": "video",
            "documentMessage": "document",
            "documentWithCaptionMessage": "document",
            "stickerMessage": "sticker",
            "locationMessage": "location",
        }
        our_type = type_map.get(msg_type_raw, "text")

        # Extract content
        body_text = ""
        media_url = ""
        caption = ""

        if our_type == "text":
            body_text = (
                message.get("conversation")
                or message.get("extendedTextMessage", {}).get("text", "")
                or ""
            )
        elif our_type == "image":
            img_msg = message.get("imageMessage", {})
            caption = img_msg.get("caption", "")
            body_text = caption or "[image]"
            media_url = img_msg.get("url", "")
        elif our_type == "audio":
            body_text = "[voice message]"
        elif our_type == "video":
            vid_msg = message.get("videoMessage", {})
            caption = vid_msg.get("caption", "")
            body_text = caption or "[video]"
        elif our_type == "document":
            doc_msg = (
                message.get("documentMessage")
                or message.get("documentWithCaptionMessage", {}).get("message", {}).get("documentMessage", {})
                or {}
            )
            body_text = doc_msg.get("fileName", "[document]")

        return {
            "instance": instance,
            "event": "message",
            "message_id": msg_id,
            "phone": phone,
            "remote_jid": remote_jid,
            "contact_name": contact_name,
            "type": our_type,
            "body": body_text,
            "caption": caption,
            "media_url": media_url,
            "raw_message": message,
            "raw_data": data,
        }

    elif event == "connection.update":
        data = body.get("data", {})
        return {
            "instance": instance,
            "event": "connection_update",
            "state": data.get("state", ""),
            "status_reason": data.get("statusReason"),
            "qr": data.get("qrcode", {}).get("base64", "") if "qrcode" in data else "",
        }

    elif event == "qrcode.updated":
        data = body.get("data", {})
        return {
            "instance": instance,
            "event": "qr_update",
            "qr": data.get("qrcode", {}).get("base64", ""),
        }

    return None


# Singleton
evolution_service = EvolutionService()
