"""
Unit tests for backend/services/email_service.py
Tests email service functionality and SendGrid integration
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.services.email_service import EmailService


class TestEmailServiceInitialization:
    """Test EmailService initialization"""
    
    def test_email_service_initialization_with_api_key(self):
        """Test EmailService initializes with SendGrid API key"""
        with patch('backend.services.email_service.settings') as mock_settings:
            with patch('backend.services.email_service.SendGridAPIClient'):
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                assert service.sg is not None
                assert service.sender_email == "sender@test.com"
                assert service.admin_email == "admin@test.com"
    
    def test_email_service_initialization_without_api_key(self):
        """Test EmailService initialization without API key"""
        with patch('backend.services.email_service.settings') as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.sender_email = "sender@test.com"
            mock_settings.admin_email = "admin@test.com"
            
            service = EmailService()
            
            assert service.sg is None
            assert service.sender_email == "sender@test.com"
            assert service.admin_email == "admin@test.com"


class TestSendEmail:
    """Test send_email functionality"""
    
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 202
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email(
                    "recipient@test.com",
                    "Test Subject",
                    "<p>Test Content</p>"
                )
                
                assert result is True
                mock_sg_instance.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_without_sendgrid_configured(self):
        """Test sending email when SendGrid is not configured"""
        with patch('backend.services.email_service.settings') as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.sender_email = "sender@test.com"
            mock_settings.admin_email = "admin@test.com"
            
            service = EmailService()
            result = await service.send_email(
                "recipient@test.com",
                "Test Subject",
                "<p>Test Content</p>"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_failure_status_code(self):
        """Test email sending with failure status code"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 500
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email(
                    "recipient@test.com",
                    "Test Subject",
                    "<p>Test Content</p>"
                )
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_exception_handling(self):
        """Test email sending with exception"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(side_effect=Exception("SendGrid error"))
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email(
                    "recipient@test.com",
                    "Test Subject",
                    "<p>Test Content</p>"
                )
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self):
        """Test sending email with plain text content type"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 200
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email(
                    "recipient@test.com",
                    "Test Subject",
                    "Plain text content",
                    content_type="text/plain"
                )
                
                assert result is True


class TestSendContactFormNotification:
    """Test send_contact_form_notification functionality"""
    
    @pytest.mark.asyncio
    async def test_send_contact_form_notification_success(self):
        """Test successful contact form notification"""
        contact_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+971501234567',
            'service': 'web_development',
            'message': 'I need a website',
            'created_at': '2024-01-15T10:30:00'
        }
        
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 202
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = await service.send_contact_form_notification(contact_data)
                    
                    assert result is True
                    mock_send.assert_called_once()
                    
                    # Verify email content includes contact details
                    call_args = mock_send.call_args
                    content = call_args[0][2]
                    assert 'John Doe' in content
                    assert 'john@example.com' in content
                    assert '+971501234567' in content
                    assert 'I need a website' in content
    
    @pytest.mark.asyncio
    async def test_send_contact_form_notification_contains_all_fields(self):
        """Test that notification contains all contact form fields"""
        contact_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '+971509876543',
            'service': 'social_media',
            'message': 'Need social media management',
            'created_at': '2024-01-15T14:00:00'
        }
        
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    await service.send_contact_form_notification(contact_data)
                    
                    call_args = mock_send.call_args
                    to_email = call_args[0][0]
                    subject = call_args[0][1]
                    content = call_args[0][2]
                    
                    # Verify recipient is admin email
                    assert to_email == mock_settings.admin_email
                    
                    # Verify subject contains name
                    assert 'Jane Smith' in subject
                    
                    # Verify content contains all fields
                    assert 'Jane Smith' in content
                    assert 'jane@example.com' in content
                    assert '+971509876543' in content
                    assert 'social_media' in content
                    assert 'Need social media management' in content
    
    @pytest.mark.asyncio
    async def test_send_contact_form_notification_html_format(self):
        """Test that notification is formatted as HTML"""
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+971501111111',
            'service': 'seo',
            'message': 'SEO services needed'
        }
        
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    await service.send_contact_form_notification(contact_data)
                    
                    call_args = mock_send.call_args
                    content = call_args[0][2]
                    
                    # Verify HTML tags present
                    assert '<html>' in content
                    assert '<body' in content
                    assert '</body>' in content
                    assert '</html>' in content
    
    @pytest.mark.asyncio
    async def test_send_contact_form_notification_without_created_at(self):
        """Test notification when created_at is missing"""
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+971501111111',
            'service': 'web_development',
            'message': 'Need website'
        }
        
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = await service.send_contact_form_notification(contact_data)
                    
                    assert result is True
                    call_args = mock_send.call_args
                    content = call_args[0][2]
                    
                    # Should handle missing created_at gracefully
                    assert 'N/A' in content or 'created_at' in contact_data


class TestEmailServiceEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_send_email_with_empty_recipient(self):
        """Test sending email with empty recipient"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_sg_instance = Mock()
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email("", "Subject", "Content")
                
                # Should handle gracefully
                assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_send_email_with_special_characters_in_subject(self):
        """Test sending email with special characters in subject"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 202
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                result = await service.send_email(
                    "test@example.com",
                    "Test 🎉 Subject with émojis",
                    "<p>Content</p>"
                )
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_with_very_long_content(self):
        """Test sending email with very long content"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 202
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                long_content = "<p>Test content</p>" * 10000
                result = await service.send_email(
                    "test@example.com",
                    "Subject",
                    long_content
                )
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_contact_form_notification_with_missing_fields(self):
        """Test contact form notification with missing optional fields"""
        minimal_contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+971501111111',
            'service': 'other',
            'message': 'Test message'
        }
        
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                with patch.object(service, 'send_email', return_value=True) as mock_send:
                    result = await service.send_contact_form_notification(minimal_contact_data)
                    
                    assert result is True
                    mock_send.assert_called_once()


class TestEmailServiceConfiguration:
    """Test email service configuration"""
    
    def test_email_service_uses_correct_sender(self):
        """Test that email service uses configured sender email"""
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "custom@sender.com"
                mock_settings.admin_email = "admin@test.com"
                
                service = EmailService()
                
                assert service.sender_email == "custom@sender.com"
    
    def test_email_service_uses_correct_admin_email(self):
        """Test that email service uses configured admin email"""
        with patch('backend.services.email_service.SendGridAPIClient'):
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "custom@admin.com"
                
                service = EmailService()
                
                assert service.admin_email == "custom@admin.com"
    
    @pytest.mark.asyncio
    async def test_multiple_emails_use_same_configuration(self):
        """Test that multiple emails use same configuration"""
        with patch('backend.services.email_service.SendGridAPIClient') as mock_sg_client:
            with patch('backend.services.email_service.settings') as mock_settings:
                mock_settings.sendgrid_api_key = "test_key"
                mock_settings.sender_email = "sender@test.com"
                mock_settings.admin_email = "admin@test.com"
                
                mock_response = Mock()
                mock_response.status_code = 202
                mock_sg_instance = Mock()
                mock_sg_instance.send = Mock(return_value=mock_response)
                mock_sg_client.return_value = mock_sg_instance
                
                service = EmailService()
                
                await service.send_email("test1@example.com", "Subject 1", "Content 1")
                await service.send_email("test2@example.com", "Subject 2", "Content 2")
                
                # Both emails should use same SendGrid instance
                assert mock_sg_instance.send.call_count == 2