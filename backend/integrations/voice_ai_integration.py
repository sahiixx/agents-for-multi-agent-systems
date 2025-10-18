"""
OpenAI Voice AI Integration - Speech-to-Text and Text-to-Speech
"""
import logging
import os
from typing import Dict, Any
from emergentintegrations.llm.openai import OpenAIChatRealtime

logger = logging.getLogger(__name__)

class VoiceAIIntegration:
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-8A3Bc7c1f91F43cE8D")
        self.realtime_chat = None
    
    def get_realtime_client(self):
        """Get OpenAI Realtime client for voice chat"""
        if not self.realtime_chat:
            self.realtime_chat = OpenAIChatRealtime(api_key=self.api_key)
        return self.realtime_chat
    
    async def create_voice_session(self) -> Dict[str, Any]:
        """Create a voice chat session"""
        try:
            client = self.get_realtime_client()
            # This will be used with WebRTC on frontend
            return {
                "status": "ready",
                "message": "Voice AI session initialized",
                "client_ready": True
            }
        except Exception as e:
            logger.error(f"Voice AI session error: {e}")
            return {"error": str(e)}
    
    def get_integration_info(self) -> Dict[str, Any]:
        """Get integration information"""
        return {
            "provider": "OpenAI Realtime",
            "capabilities": [
                "Real-time voice chat",
                "Speech-to-text",
                "Text-to-speech",
                "WebRTC support"
            ],
            "status": "available" if self.api_key else "not_configured"
        }

voice_ai_integration = VoiceAIIntegration()
