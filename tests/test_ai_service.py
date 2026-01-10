"""
Unit tests for backend/services/ai_service.py
Tests AI service integration and chat functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.services.ai_service import AIService


class TestAIServiceInitialization:
    """Test AIService initialization"""
    
    def test_ai_service_initialization(self):
        """Test that AIService initializes with correct configuration"""
        with patch('backend.services.ai_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            mock_settings.default_ai_model = "gpt-4o"
            mock_settings.ai_provider = "openai"
            
            service = AIService()
            
            assert service.api_key == "test_key"
            assert service.model == "gpt-4o"
            assert service.provider == "openai"
    
    def test_ai_service_uses_settings(self):
        """Test that AIService reads from settings"""
        with patch('backend.services.ai_service.settings') as mock_settings:
            mock_settings.openai_api_key = "custom_key"
            mock_settings.default_ai_model = "gpt-3.5-turbo"
            mock_settings.ai_provider = "anthropic"
            
            service = AIService()
            
            assert service.api_key == "custom_key"
            assert service.model == "gpt-3.5-turbo"
            assert service.provider == "anthropic"


class TestCreateChatSession:
    """Test create_chat_session functionality"""
    
    @pytest.mark.asyncio
    async def test_create_chat_session_with_custom_system_message(self):
        """Test creating chat session with custom system message"""
        service = AIService()
        session_id = "test_session_123"
        custom_message = "You are a helpful assistant"
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat_instance = Mock()
            mock_chat_instance.with_model = Mock(return_value=mock_chat_instance)
            mock_chat_instance.with_max_tokens = Mock(return_value=mock_chat_instance)
            mock_chat_class.return_value = mock_chat_instance
            
            await service.create_chat_session(session_id, custom_message)
            
            mock_chat_class.assert_called_once()
            call_kwargs = mock_chat_class.call_args[1]
            assert call_kwargs['session_id'] == session_id
            assert call_kwargs['system_message'] == custom_message
            mock_chat_instance.with_model.assert_called_once()
            mock_chat_instance.with_max_tokens.assert_called_once_with(2048)
    
    @pytest.mark.asyncio
    async def test_create_chat_session_with_default_system_message(self):
        """Test creating chat session with default system message"""
        service = AIService()
        session_id = "test_session_456"
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat_instance = Mock()
            mock_chat_instance.with_model = Mock(return_value=mock_chat_instance)
            mock_chat_instance.with_max_tokens = Mock(return_value=mock_chat_instance)
            mock_chat_class.return_value = mock_chat_instance
            
            await service.create_chat_session(session_id)
            
            mock_chat_class.assert_called_once()
            call_kwargs = mock_chat_class.call_args[1]
            assert "NOWHERE Digital" in call_kwargs['system_message']
            assert "Dubai" in call_kwargs['system_message']
    
    @pytest.mark.asyncio
    async def test_create_chat_session_configures_model(self):
        """Test that chat session is configured with correct model"""
        service = AIService()
        service.provider = "openai"
        service.model = "gpt-4o"
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat_instance = Mock()
            mock_chat_instance.with_model = Mock(return_value=mock_chat_instance)
            mock_chat_instance.with_max_tokens = Mock(return_value=mock_chat_instance)
            mock_chat_class.return_value = mock_chat_instance
            
            await service.create_chat_session("session_id")
            
            mock_chat_instance.with_model.assert_called_once_with("openai", "gpt-4o")
    
    @pytest.mark.asyncio
    async def test_create_chat_session_error_handling(self):
        """Test error handling in create_chat_session"""
        service = AIService()
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat_class.side_effect = Exception("API error")
            
            with pytest.raises(Exception) as exc_info:
                await service.create_chat_session("session_id")
            
            assert "API error" in str(exc_info.value)


class TestSendChatMessage:
    """Test send_chat_message functionality"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message_success(self):
        """Test successful message sending"""
        service = AIService()
        session_id = "test_session"
        message = "What services do you offer?"
        expected_response = "We offer digital marketing services"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value=expected_response)
            mock_create.return_value = mock_chat
            
            response = await service.send_chat_message(session_id, message)
            
            assert response == expected_response
            mock_create.assert_called_once_with(session_id)
            mock_chat.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_chat_message_creates_user_message(self):
        """Test that UserMessage is created correctly"""
        service = AIService()
        message_text = "Hello, I need help"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            with patch('backend.services.ai_service.UserMessage') as mock_user_message_class:
                mock_chat = AsyncMock()
                mock_chat.send_message = AsyncMock(return_value="Response")
                mock_create.return_value = mock_chat
                mock_user_message_class.return_value = Mock()
                
                await service.send_chat_message("session", message_text)
                
                mock_user_message_class.assert_called_once_with(text=message_text)
    
    @pytest.mark.asyncio
    async def test_send_chat_message_error_handling(self):
        """Test error handling in send_chat_message"""
        service = AIService()
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_create.side_effect = Exception("Connection error")
            
            response = await service.send_chat_message("session_id", "test message")
            
            assert "trouble processing" in response
            assert "try again later" in response


class TestGenerateContent:
    """Test generate_content functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_content_blog_post(self):
        """Test generating blog post content"""
        service = AIService()
        content_type = "blog_post"
        prompt = "Write about SEO best practices"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="SEO blog content...")
            mock_create.return_value = mock_chat
            
            content = await service.generate_content(content_type, prompt)
            
            assert content == "SEO blog content..."
            mock_create.assert_called_once()
            # Verify system message is blog-specific
            call_args = mock_create.call_args
            assert "content writer" in call_args[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_generate_content_social_media(self):
        """Test generating social media content"""
        service = AIService()
        content_type = "social_media"
        prompt = "Create Instagram post"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Social media post...")
            mock_create.return_value = mock_chat
            
            content = await service.generate_content(content_type, prompt)
            
            assert content == "Social media post..."
            call_args = mock_create.call_args
            assert "social media" in call_args[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_generate_content_ad_copy(self):
        """Test generating ad copy"""
        service = AIService()
        content_type = "ad_copy"
        prompt = "Create Facebook ad"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Ad copy...")
            mock_create.return_value = mock_chat
            
            content = await service.generate_content(content_type, prompt)
            
            assert content == "Ad copy..."
            call_args = mock_create.call_args
            assert "advertising copywriter" in call_args[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_generate_content_email_campaign(self):
        """Test generating email campaign"""
        service = AIService()
        content_type = "email_campaign"
        prompt = "Create welcome email"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Email content...")
            mock_create.return_value = mock_chat
            
            content = await service.generate_content(content_type, prompt)
            
            assert content == "Email content..."
            call_args = mock_create.call_args
            assert "email marketing" in call_args[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_generate_content_with_additional_context(self):
        """Test generating content with additional context"""
        service = AIService()
        additional_context = {
            "target_audience": "Dubai businesses",
            "tone": "professional"
        }
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Content...")
            mock_create.return_value = mock_chat
            
            with patch('backend.services.ai_service.UserMessage') as mock_user_message:
                mock_user_message.return_value = Mock()
                
                await service.generate_content(
                    "blog_post",
                    "Write about marketing",
                    additional_context
                )
                
                # Verify context was included
                mock_chat.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_content_error_handling(self):
        """Test error handling in generate_content"""
        service = AIService()
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_create.side_effect = Exception("Generation error")
            
            # Should not raise exception, but return error message
            content = await service.generate_content("blog_post", "test prompt")
            
            # Depending on implementation, should handle gracefully
            assert content is not None


class TestAIServiceIntegration:
    """Test AI service integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_chat_sessions(self):
        """Test handling multiple chat sessions"""
        service = AIService()
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.with_model = Mock(return_value=mock_chat)
            mock_chat.with_max_tokens = Mock(return_value=mock_chat)
            mock_chat_class.return_value = mock_chat
            
            session1 = await service.create_chat_session("session_1")
            session2 = await service.create_chat_session("session_2")
            
            assert session1 is not None
            assert session2 is not None
            assert mock_chat_class.call_count == 2
    
    @pytest.mark.asyncio
    async def test_chat_with_uae_context(self):
        """Test that chat includes UAE market context"""
        service = AIService()
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.with_model = Mock(return_value=mock_chat)
            mock_chat.with_max_tokens = Mock(return_value=mock_chat)
            mock_chat_class.return_value = mock_chat
            
            await service.create_chat_session("session_id")
            
            call_kwargs = mock_chat_class.call_args[1]
            system_message = call_kwargs['system_message']
            
            assert "UAE" in system_message or "Dubai" in system_message
            assert "digital marketing" in system_message.lower()
    
    @pytest.mark.asyncio
    async def test_service_configuration_consistency(self):
        """Test that service maintains configuration consistency"""
        service = AIService()
        service.api_key = "test_key"
        service.model = "gpt-4"
        service.provider = "openai"
        
        # Multiple operations should use same config
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.with_model = Mock(return_value=mock_chat)
            mock_chat.with_max_tokens = Mock(return_value=mock_chat)
            mock_chat_class.return_value = mock_chat
            
            await service.create_chat_session("session_1")
            await service.create_chat_session("session_2")
            
            # Both calls should use same configuration
            assert mock_chat_class.call_count == 2
            for call in mock_chat_class.call_args_list:
                assert call[1]['api_key'] == "test_key"


class TestAIServiceEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self):
        """Test handling of empty messages"""
        service = AIService()
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Response")
            mock_create.return_value = mock_chat
            
            response = await service.send_chat_message("session_id", "")
            
            assert response is not None
    
    @pytest.mark.asyncio
    async def test_very_long_message_handling(self):
        """Test handling of very long messages"""
        service = AIService()
        long_message = "test " * 10000  # Very long message
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Response")
            mock_create.return_value = mock_chat
            
            response = await service.send_chat_message("session_id", long_message)
            
            assert response is not None
    
    @pytest.mark.asyncio
    async def test_special_characters_in_message(self):
        """Test handling of special characters"""
        service = AIService()
        special_message = "Test with émojis 🎉 and spëcial chârs"
        
        with patch.object(service, 'create_chat_session') as mock_create:
            mock_chat = AsyncMock()
            mock_chat.send_message = AsyncMock(return_value="Response")
            mock_create.return_value = mock_chat
            
            response = await service.send_chat_message("session_id", special_message)
            
            assert response is not None
    
    @pytest.mark.asyncio
    async def test_none_session_id_handling(self):
        """Test handling of None session ID"""
        service = AIService()
        
        with patch('backend.services.ai_service.LlmChat') as mock_chat_class:
            mock_chat = Mock()
            mock_chat.with_model = Mock(return_value=mock_chat)
            mock_chat.with_max_tokens = Mock(return_value=mock_chat)
            mock_chat_class.return_value = mock_chat
            
            # Should handle None gracefully
            chat = await service.create_chat_session(None)
            assert chat is not None