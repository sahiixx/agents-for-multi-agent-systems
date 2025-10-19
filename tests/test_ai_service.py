"""
Comprehensive unit tests for backend/services/ai_service.py
Tests AI service functionality including chat and content generation
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from emergentintegrations.llm.chat import LlmChat, UserMessage


class TestAIServiceInitialization:
    """Test AIService initialization"""
    
    def test_ai_service_creation(self):
        """Test AIService can be created"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        assert service is not None
        assert hasattr(service, "api_key")
        assert hasattr(service, "model")
        assert hasattr(service, "provider")
    
    def test_ai_service_uses_config_settings(self):
        """Test AIService uses configuration from settings"""
        from backend.services.ai_service import AIService
        from backend.config import settings
        
        service = AIService()
        assert service.api_key == settings.openai_api_key
        assert service.model == settings.default_ai_model
        assert service.provider == settings.ai_provider
    
    def test_global_ai_service_instance(self):
        """Test global ai_service instance is available"""
        from backend.services.ai_service import ai_service
        
        assert ai_service is not None


class TestCreateChatSession:
    """Test create_chat_session method"""
    
    @pytest.mark.asyncio
    async def test_create_chat_session_with_default_system_message(self):
        """Test creating chat session with default system message"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        chat = await service.create_chat_session("test_session_123")
        
        assert chat is not None
        assert isinstance(chat, LlmChat)
        assert chat.session_id == "test_session_123"
    
    @pytest.mark.asyncio
    async def test_create_chat_session_with_custom_system_message(self):
        """Test creating chat session with custom system message"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        custom_message = "You are a test assistant"
        chat = await service.create_chat_session("test_session_456", custom_message)
        
        assert chat is not None
        assert chat.system_message == custom_message
    
    @pytest.mark.asyncio
    async def test_chat_session_configures_model(self):
        """Test chat session is configured with correct model"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        chat = await service.create_chat_session("test_session_789")
        
        # Model should be configured
        assert hasattr(chat, "model")
        assert chat.model[0] == service.provider
        assert chat.model[1] == service.model
    
    @pytest.mark.asyncio
    async def test_chat_session_configures_max_tokens(self):
        """Test chat session is configured with max tokens"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        chat = await service.create_chat_session("test_session")
        
        assert chat.max_tokens == 2048
    
    @pytest.mark.asyncio
    async def test_create_chat_session_handles_errors(self):
        """Test error handling in chat session creation"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        
        with patch("emergentintegrations.llm.chat.LlmChat", side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                await service.create_chat_session("test_session")
            
            assert "API Error" in str(exc_info.value)


class TestSendChatMessage:
    """Test send_chat_message method"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message_success(self):
        """Test sending chat message successfully"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        response = await service.send_chat_message("test_session", "Hello AI")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_send_chat_message_returns_meaningful_response(self):
        """Test chat message returns meaningful response"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        response = await service.send_chat_message("test_session", "Tell me about your services")
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_send_chat_message_handles_errors(self):
        """Test error handling when sending message fails"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        
        with patch.object(service, "create_chat_session", side_effect=Exception("Connection failed")):
            response = await service.send_chat_message("test_session", "Hello")
            
            # Should return error message instead of raising
            assert "sorry" in response.lower()
            assert "trouble" in response.lower() or "error" in response.lower()
    
    @pytest.mark.asyncio
    async def test_send_chat_message_with_empty_message(self):
        """Test sending empty message"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        response = await service.send_chat_message("test_session", "")
        
        # Should handle gracefully
        assert isinstance(response, str)


class TestGenerateContent:
    """Test generate_content method"""
    
    @pytest.mark.asyncio
    async def test_generate_blog_post(self):
        """Test generating blog post content"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "blog_post",
            "Write about digital marketing trends in Dubai"
        )
        
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0
    
    @pytest.mark.asyncio
    async def test_generate_social_media_content(self):
        """Test generating social media content"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "social_media",
            "Create a post about web development services"
        )
        
        assert isinstance(content, str)
        assert len(content) > 0
    
    @pytest.mark.asyncio
    async def test_generate_ad_copy(self):
        """Test generating ad copy"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "ad_copy",
            "Promote our SEO services"
        )
        
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_email_campaign(self):
        """Test generating email campaign content"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "email_campaign",
            "Welcome new customers to our platform"
        )
        
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_web_copy(self):
        """Test generating web copy"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "web_copy",
            "Homepage hero section about AI solutions"
        )
        
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_seo_content(self):
        """Test generating SEO content"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "seo_content",
            "Write about AI business automation for UAE market"
        )
        
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_content_with_additional_context(self):
        """Test generating content with additional context"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        context = {
            "target_audience": "Small businesses in Dubai",
            "tone": "Professional but friendly",
            "word_count": 500
        }
        
        content = await service.generate_content(
            "blog_post",
            "Write about the benefits of AI automation",
            additional_context=context
        )
        
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_content_unknown_type(self):
        """Test generating content with unknown content type"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        content = await service.generate_content(
            "unknown_type",
            "Test prompt"
        )
        
        # Should still work with default system message
        assert isinstance(content, str)
    
    @pytest.mark.asyncio
    async def test_generate_content_handles_errors(self):
        """Test error handling in content generation"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        
        with patch.object(service, "create_chat_session", side_effect=Exception("API Error")):
            # Should handle error gracefully
            content = await service.generate_content("blog_post", "Test")
            # If it returns something, should be error message
            assert isinstance(content, str)


class TestAIServiceIntegration:
    """Integration tests for AI service"""
    
    @pytest.mark.asyncio
    async def test_multiple_chat_sessions(self):
        """Test creating multiple chat sessions"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        
        chat1 = await service.create_chat_session("session1")
        chat2 = await service.create_chat_session("session2")
        
        assert chat1.session_id == "session1"
        assert chat2.session_id == "session2"
    
    @pytest.mark.asyncio
    async def test_chat_and_content_generation(self):
        """Test both chat and content generation work"""
        from backend.services.ai_service import AIService
        
        service = AIService()
        
        # Send chat message
        chat_response = await service.send_chat_message("test", "Hello")
        assert isinstance(chat_response, str)
        
        # Generate content
        content = await service.generate_content("blog_post", "Test")
        assert isinstance(content, str)


class TestAIServiceConfiguration:
    """Test AI service configuration"""
    
    def test_ai_service_respects_settings(self):
        """Test that AI service respects configuration settings"""
        from backend.services.ai_service import AIService
        from backend.config import settings
        
        service = AIService()
        
        assert service.api_key == settings.openai_api_key
        assert service.model == settings.default_ai_model
        assert service.provider == settings.ai_provider
    
    @patch("backend.config.settings")
    def test_ai_service_with_custom_settings(self, mock_settings):
        """Test AI service with custom settings"""
        mock_settings.openai_api_key = "custom_key"
        mock_settings.default_ai_model = "custom_model"
        mock_settings.ai_provider = "custom_provider"
        
        from backend.services.ai_service import AIService
        service = AIService()
        
        assert service.api_key == "custom_key"
        assert service.model == "custom_model"
        assert service.provider == "custom_provider"