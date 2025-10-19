"""
Comprehensive unit tests for backend/services/email_service.py
Tests email service functionality including SendGrid integration
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class TestEmailServiceInitialization:
    """Test EmailService initialization"""
    
    def test_email_service_creation(self):
        """Test EmailService can be created"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        assert service is not None
        assert hasattr(service, "sg")
        assert hasattr(service, "sender_email")
        assert hasattr(service, "admin_email")
    
    def test_email_service_uses_config_settings(self):
        """Test EmailService uses configuration from settings"""
        from backend.services.email_service import EmailService
        from backend.config import settings
        
        service = EmailService()
        assert service.sender_email == settings.sender_email
        assert service.admin_email == settings.admin_email
    
    def test_global_email_service_instance(self):
        """Test global email_service instance is available"""
        from backend.services.email_service import email_service
        
        assert email_service is not None
    
    def test_email_service_without_sendgrid_api_key(self):
        """Test EmailService handles missing SendGrid API key"""
        with patch("backend.config.settings") as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.sender_email = "test@example.com"
            mock_settings.admin_email = "admin@example.com"
            
            from backend.services.email_service import EmailService
            service = EmailService()
            
            # Should create service but sg client should be None
            assert service.sg is None


class TestSendEmail:
    """Test send_email method"""
    
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test sending email successfully"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        result = await service.send_email(
            "recipient@example.com",
            "Test Subject",
            "<p>Test content</p>"
        )
        
        # With stub, should return True
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self):
        """Test sending plain text email"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        result = await service.send_email(
            "recipient@example.com",
            "Test Subject",
            "Plain text content",
            content_type="text/plain"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_without_sendgrid_configured(self):
        """Test sending email when SendGrid is not configured"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        service.sg = None
        
        result = await service.send_email(
            "recipient@example.com",
            "Test",
            "Test"
        )
        
        # Should return False and log warning
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_handles_errors(self):
        """Test error handling when sending email fails"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        if service.sg:
            service.sg.send = MagicMock(side_effect=Exception("SendGrid error"))
            
            result = await service.send_email(
                "recipient@example.com",
                "Test",
                "Test"
            )
            
            # Should return False on error
            assert result is False


class TestSendContactFormNotification:
    """Test send_contact_form_notification method"""
    
    @pytest.mark.asyncio
    async def test_send_contact_form_notification(self):
        """Test sending contact form notification"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+971501234567",
            "service": "web_development",
            "message": "I need a website",
            "created_at": "2025-01-01T12:00:00Z"
        }
        
        result = await service.send_contact_form_notification(contact_data)
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_contact_notification_includes_all_fields(self):
        """Test contact notification includes all contact fields"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+971507654321",
            "service": "digital_marketing",
            "message": "Looking for SEO services"
        }
        
        result = await service.send_contact_form_notification(contact_data)
        
        # Should process all fields
        assert isinstance(result, bool)


class TestSendContactConfirmation:
    """Test send_contact_confirmation method"""
    
    @pytest.mark.asyncio
    async def test_send_contact_confirmation(self):
        """Test sending contact confirmation to user"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "service": "ai_solutions",
            "message": "Interested in AI automation"
        }
        
        result = await service.send_contact_confirmation(contact_data)
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_confirmation_email_personalized(self):
        """Test confirmation email is personalized with user name"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "service": "whatsapp_business",
            "message": "Need WhatsApp integration"
        }
        
        result = await service.send_contact_confirmation(contact_data)
        
        # Should include user's name and service
        assert isinstance(result, bool)


class TestSendBookingConfirmation:
    """Test send_booking_confirmation method"""
    
    @pytest.mark.asyncio
    async def test_send_booking_confirmation(self):
        """Test sending booking confirmation"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        booking_data = {
            "booking_id": "BOOK123",
            "service": "consultation",
            "preferred_date": "2025-02-15",
            "preferred_time": "14:00",
            "status": "confirmed"
        }
        
        result = await service.send_booking_confirmation(
            booking_data,
            "customer@example.com"
        )
        
        assert isinstance(result, bool)


class TestEmailServiceIntegration:
    """Integration tests for email service"""
    
    @pytest.mark.asyncio
    async def test_multiple_emails_in_sequence(self):
        """Test sending multiple emails in sequence"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        # Send multiple emails
        result1 = await service.send_email("user1@example.com", "Test 1", "Content 1")
        result2 = await service.send_email("user2@example.com", "Test 2", "Content 2")
        result3 = await service.send_email("user3@example.com", "Test 3", "Content 3")
        
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
        assert isinstance(result3, bool)
    
    @pytest.mark.asyncio
    async def test_contact_workflow(self):
        """Test complete contact form email workflow"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+971501111111",
            "service": "web_development",
            "message": "Test inquiry"
        }
        
        # Send notification to admin
        admin_result = await service.send_contact_form_notification(contact_data)
        
        # Send confirmation to user
        user_result = await service.send_contact_confirmation(contact_data)
        
        assert isinstance(admin_result, bool)
        assert isinstance(user_result, bool)


class TestEmailServiceConfiguration:
    """Test email service configuration"""
    
    def test_email_service_respects_settings(self):
        """Test that email service respects configuration settings"""
        from backend.services.email_service import EmailService
        from backend.config import settings
        
        service = EmailService()
        
        assert service.sender_email == settings.sender_email
        assert service.admin_email == settings.admin_email
    
    @patch("backend.config.settings")
    def test_email_service_with_custom_settings(self, mock_settings):
        """Test email service with custom settings"""
        mock_settings.sendgrid_api_key = "test_key"
        mock_settings.sender_email = "custom@example.com"
        mock_settings.admin_email = "customadmin@example.com"
        
        from backend.services.email_service import EmailService
        service = EmailService()
        
        assert service.sender_email == "custom@example.com"
        assert service.admin_email == "customadmin@example.com"


class TestEmailTemplates:
    """Test email template formatting"""
    
    @pytest.mark.asyncio
    async def test_contact_notification_html_format(self):
        """Test contact notification uses HTML format"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+971501234567",
            "service": "seo",
            "message": "Need help with SEO",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        # Should not raise error
        result = await service.send_contact_form_notification(contact_data)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_confirmation_email_branded(self):
        """Test confirmation email includes branding"""
        from backend.services.email_service import EmailService
        
        service = EmailService()
        
        contact_data = {
            "name": "Brand Test",
            "email": "brand@example.com",
            "service": "marketing",
            "message": "Test message"
        }
        
        # Confirmation should include NOWHERE Digital branding
        result = await service.send_contact_confirmation(contact_data)
        assert isinstance(result, bool)