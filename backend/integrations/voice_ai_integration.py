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
        """
        Initialize the VoiceAIIntegration instance and prepare lazy client state.
        
        Attributes:
            api_key (str): API key loaded from the EMERGENT_LLM_KEY environment variable or a fallback placeholder if not set.
            realtime_chat: Initially None; will hold the lazily created realtime OpenAI chat client once initialized.
        """
        self.api_key = os.getenv("EMERGENT_LLM_KEY", "sk-emergent-8A3Bc7c1f91F43cE8D")
        self.realtime_chat = None
    
    def get_realtime_client(self):
        """
        Return the OpenAI realtime chat client used for voice chat.
        
        Creates and caches an OpenAIChatRealtime client on first call and returns the stored instance.
        
        Returns:
            OpenAIChatRealtime: The realtime chat client instance for voice and realtime interactions.
        """
        if not self.realtime_chat:
            self.realtime_chat = OpenAIChatRealtime(api_key=self.api_key)
        return self.realtime_chat
    
    async def create_voice_session(self) -> Dict[str, Any]:
        """
        Initialize and prepare a realtime voice chat session for WebRTC usage.
        
        Returns:
            dict: If successful, a dictionary with keys:
                - "status": "ready"
                - "message": a human-readable initialization message
                - "client_ready": True
            If an error occurs, a dictionary with:
                - "error": the error message string
        """
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
        """
        Provide metadata about the voice AI integration.
        
        Returns:
            info (Dict[str, Any]): Dictionary with keys:
                - "provider": Name of the integration provider (e.g., "OpenAI Realtime").
                - "capabilities": List of supported features (e.g., "Real-time voice chat", "Speech-to-text", "Text-to-speech", "WebRTC support").
                - "status": "available" if an API key is configured, "not_configured" otherwise.
        """
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