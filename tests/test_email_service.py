"""
Unit tests for backend/services/email_service.py
Tests email service functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.services.email_service import EmailService, email_service


class TestEmailService:
    """Test suite for Email Service"""
    
    @pytest.fixture
    def service(self):
        """Create email service instance"""
        with patch('backend.services.email_service.SendGridAPIClient'):
            return EmailService()
    
    def test_initialization(self, service):
        """Test email service initialization"""
        assert service is not None
        assert hasattr(service, 'api_key')
        assert hasattr(service, 'from_email')
        
    @pytest.mark.asyncio
    async def test_send_email_basic(self, service):
        """Test basic email sending"""
        with patch.object(service, 'sg', Mock()) as mock_sg:
            mock_response = Mock()
            mock_response.status_code = 202
            mock_sg.send = Mock(return_value=mock_response)
            
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                content="Test content"
            )
            
            assert result is not None
            
    @pytest.mark.asyncio
    async def test_send_email_error_handling(self, service):
        """Test email error handling"""
        service.sg = None
        
        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            content="Test"
        )
        
        # Should handle gracefully
        assert result is not None


class TestEmailServiceGlobalInstance:
    """Test global email service instance"""
    
    def test_global_instance_exists(self):
        """Test that global email_service exists"""
        assert email_service is not None
        assert isinstance(email_service, EmailService)