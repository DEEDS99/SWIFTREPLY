"""
SwiftReply — Google Gemini AI Service
======================================
Handles multimodal AI responses for:
- Text messages
- Image analysis and replies
- Audio transcription and replies
- Video analysis and replies
- Context-aware conversation history
"""

import os
import base64
import logging
import httpx
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("swiftreply.gemini")


class GeminiService:
    """Google Gemini multimodal AI service."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            logger.warning("No Gemini API key configured")
            self.model = None

    def _get_model(self, api_key: Optional[str] = None):
        """Get model with optional per-org API key override."""
        if api_key and api_key != self.api_key:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(self.model_name)
        return self.model

    async def generate_text_reply(
        self,
        incoming_text: str,
        conversation_history: list,
        system_prompt: str,
        contact_name: str = "Customer",
        org_api_key: Optional[str] = None,
    ) -> dict:
        """Generate AI reply for a text message."""
        try:
            model = self._get_model(org_api_key)
            if not model:
                return {"success": False, "error": "AI not configured", "reply": None}

            # Build conversation context
            history_text = ""
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "Customer" if msg.get("direction") == "inbound" else "Agent"
                history_text += f"{role}: {msg.get('body', '')}\n"

            prompt = f"""{system_prompt}

Contact name: {contact_name}

Recent conversation:
{history_text}

New message from customer: {incoming_text}

Reply as the business agent. Be helpful, professional, and concise. Reply directly without any prefix."""

            response = model.generate_content(prompt)
            return {
                "success": True,
                "reply": response.text.strip(),
                "ai_generated": True,
                "confidence": 90,
            }
        except Exception as e:
            logger.error(f"Gemini text reply error: {e}")
            return {"success": False, "error": str(e), "reply": None}

    async def analyze_image_and_reply(
        self,
        image_url: str,
        caption: Optional[str],
        conversation_history: list,
        system_prompt: str,
        contact_name: str = "Customer",
        org_api_key: Optional[str] = None,
    ) -> dict:
        """Analyze an incoming image and generate a contextual reply."""
        try:
            model = self._get_model(org_api_key)
            if not model:
                return {"success": False, "error": "AI not configured", "reply": None}

            # Download image
            async with httpx.AsyncClient(timeout=30) as client:
                img_response = await client.get(image_url)
                img_data = img_response.content
                content_type = img_response.headers.get("content-type", "image/jpeg")

            # Convert to base64 for Gemini
            img_b64 = base64.b64encode(img_data).decode()

            history_text = "\n".join([
                f"{'Customer' if m.get('direction') == 'inbound' else 'Agent'}: {m.get('body', '')}"
                for m in conversation_history[-5:]
            ])

            prompt_parts = [
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": img_b64
                    }
                },
                f"""{system_prompt}

Contact name: {contact_name}
Image caption from customer: {caption or '(no caption)'}

Recent conversation:
{history_text}

The customer sent you the above image. Describe what you see, understand the customer's intent, and provide a helpful business reply. Reply directly."""
            ]

            response = model.generate_content(prompt_parts)
            analysis = response.text.strip()

            return {
                "success": True,
                "reply": analysis,
                "ai_analysis": analysis,
                "ai_generated": True,
                "confidence": 85,
            }
        except Exception as e:
            logger.error(f"Gemini image analysis error: {e}")
            return {"success": False, "error": str(e), "reply": None}

    async def transcribe_and_reply_audio(
        self,
        audio_url: str,
        conversation_history: list,
        system_prompt: str,
        contact_name: str = "Customer",
        org_api_key: Optional[str] = None,
    ) -> dict:
        """Transcribe audio message and generate reply."""
        try:
            model = self._get_model(org_api_key)
            if not model:
                return {"success": False, "error": "AI not configured", "reply": None}

            async with httpx.AsyncClient(timeout=60) as client:
                audio_response = await client.get(audio_url)
                audio_data = audio_response.content
                content_type = audio_response.headers.get("content-type", "audio/ogg")

            audio_b64 = base64.b64encode(audio_data).decode()

            history_text = "\n".join([
                f"{'Customer' if m.get('direction') == 'inbound' else 'Agent'}: {m.get('body', '')}"
                for m in conversation_history[-5:]
            ])

            prompt_parts = [
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": audio_b64
                    }
                },
                f"""{system_prompt}

Contact name: {contact_name}

Recent conversation:
{history_text}

First, transcribe what the customer said in the audio. Then provide a helpful business reply.

Format your response as:
TRANSCRIPTION: [what the customer said]
REPLY: [your business reply]"""
            ]

            response = model.generate_content(prompt_parts)
            result_text = response.text.strip()

            # Parse transcription and reply
            transcription = ""
            reply = result_text
            if "TRANSCRIPTION:" in result_text and "REPLY:" in result_text:
                parts = result_text.split("REPLY:")
                transcription = parts[0].replace("TRANSCRIPTION:", "").strip()
                reply = parts[1].strip() if len(parts) > 1 else result_text

            return {
                "success": True,
                "reply": reply,
                "ai_analysis": f"Audio transcription: {transcription}",
                "transcription": transcription,
                "ai_generated": True,
                "confidence": 80,
            }
        except Exception as e:
            logger.error(f"Gemini audio transcription error: {e}")
            return {"success": False, "error": str(e), "reply": None}

    async def analyze_video_and_reply(
        self,
        video_url: str,
        caption: Optional[str],
        conversation_history: list,
        system_prompt: str,
        contact_name: str = "Customer",
        org_api_key: Optional[str] = None,
    ) -> dict:
        """Analyze video and generate contextual reply."""
        try:
            model = self._get_model(org_api_key)
            if not model:
                return {"success": False, "error": "AI not configured", "reply": None}

            async with httpx.AsyncClient(timeout=120) as client:
                video_response = await client.get(video_url)
                video_data = video_response.content
                content_type = video_response.headers.get("content-type", "video/mp4")

            video_b64 = base64.b64encode(video_data).decode()

            history_text = "\n".join([
                f"{'Customer' if m.get('direction') == 'inbound' else 'Agent'}: {m.get('body', '')}"
                for m in conversation_history[-5:]
            ])

            prompt_parts = [
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": video_b64
                    }
                },
                f"""{system_prompt}

Contact name: {contact_name}
Video caption: {caption or '(no caption)'}

Recent conversation:
{history_text}

Analyze this video the customer sent. Understand what they're showing or asking. Provide a professional business reply. Reply directly."""
            ]

            response = model.generate_content(prompt_parts)

            return {
                "success": True,
                "reply": response.text.strip(),
                "ai_analysis": response.text.strip(),
                "ai_generated": True,
                "confidence": 78,
            }
        except Exception as e:
            logger.error(f"Gemini video analysis error: {e}")
            return {"success": False, "error": str(e), "reply": None}

    async def process_incoming_message(
        self,
        message_type: str,
        content: dict,
        conversation_history: list,
        system_prompt: str,
        contact_name: str,
        org_api_key: Optional[str] = None,
    ) -> dict:
        """
        Unified entry point for processing any incoming message type.
        message_type: text | image | audio | video | document
        """
        if message_type == "text":
            return await self.generate_text_reply(
                incoming_text=content.get("body", ""),
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                contact_name=contact_name,
                org_api_key=org_api_key,
            )
        elif message_type == "image":
            return await self.analyze_image_and_reply(
                image_url=content.get("url", ""),
                caption=content.get("caption"),
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                contact_name=contact_name,
                org_api_key=org_api_key,
            )
        elif message_type == "audio":
            return await self.transcribe_and_reply_audio(
                audio_url=content.get("url", ""),
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                contact_name=contact_name,
                org_api_key=org_api_key,
            )
        elif message_type == "video":
            return await self.analyze_video_and_reply(
                video_url=content.get("url", ""),
                caption=content.get("caption"),
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                contact_name=contact_name,
                org_api_key=org_api_key,
            )
        else:
            return await self.generate_text_reply(
                incoming_text=f"[{message_type} message received]",
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                contact_name=contact_name,
                org_api_key=org_api_key,
            )


# Singleton instance
gemini_service = GeminiService()
