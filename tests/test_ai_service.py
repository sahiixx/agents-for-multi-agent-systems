"""
Unit tests for backend/services/ai_service.py
Tests AI service functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.services.ai_service import AIService, ai_service


class TestAIService:
    """Test suite for AI Service"""
    
    @pytest.fixture
    def service(self):
        """Create AI service instance"""
        return AIService()
    
    def test_initialization(self, service):
        """Test AI service initialization"""
        assert service is not None
        assert hasattr(service, 'api_key')
        
    @pytest.mark.asyncio
    @patch('backend.services.ai_service.LlmChat')
    async def test_generate_content(self, mock_chat_class, service):
        """Test content generation"""
        mock_chat = Mock()
        mock_chat.with_model = Mock(return_value=mock_chat)
        mock_chat.send_message = AsyncMock(return_value="Generated content")
        mock_chat_class.return_value = mock_chat
        
        result = await service.generate_content("Test prompt")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    @pytest.mark.asyncio
    async def test_generate_content_error_handling(self, service):
        """Test error handling in content generation"""
        with patch('backend.services.ai_service.LlmChat', side_effect=Exception("API Error")):
            result = await service.generate_content("Test prompt")
            
            # Should return a fallback response
            assert isinstance(result, str)


class TestAIServiceGlobalInstance:
    """Test global AI service instance"""
    
    def test_global_instance_exists(self):
        """Test that global ai_service exists"""
        assert ai_service is not None
        assert isinstance(ai_service, AIService)