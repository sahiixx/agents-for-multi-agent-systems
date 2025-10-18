"""
Unit Tests for SendGrid Email Integration
Tests email sending, template emails, and notification functionality
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import os
from backend.integrations.sendgrid_integration import SendGridIntegration, sendgrid_integration


class TestSendGridIntegration:
    """Comprehensive test suite for SendGrid email integration"""
    
    def test_initialization_with_api_key(self):
        """Test SendGrid initializes correctly with API key"""
        with patch.dict(os.environ, {
            'SENDGRID_API_KEY': 'test_key_123',
            'SENDGRID_FROM_EMAIL': 'test@example.com'
        }):
            integration = SendGridIntegration()
            assert integration.api_key == 'test_key_123'
            assert integration.from_email == 'test@example.com'
            assert integration.client is not None
    
    def test_initialization_without_api_key(self):
        """Test SendGrid initializes without client when no API key"""
        with patch.dict(os.environ, {}, clear=True):
            integration = SendGridIntegration()
            assert integration.api_key is None
            assert integration.client is None
            assert integration.from_email == 'noreply@nowheredigital.ae'
    
    def test_initialization_default_from_email(self):
        """Test default from_email when not specified"""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'key'}, clear=True):
            integration = SendGridIntegration()
            assert integration.from_email == 'noreply@nowheredigital.ae'
    
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending with HTML content"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        # Mock SendGrid client and response
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='recipient@example.com',
            subject='Test Subject',
            html_content='<h1>Test Email</h1>'
        )
        
        assert result['status_code'] == 202
        assert result['success'] is True
        mock_client.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self):
        """Test email sending with both HTML and plain text content"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>HTML</p>',
            plain_text='Plain text'
        )
        
        assert result['success'] is True
        assert result['status_code'] == 202
    
    @pytest.mark.asyncio
    async def test_send_email_no_client_configured(self):
        """Test email sending fails gracefully when client not configured"""
        integration = SendGridIntegration()
        integration.client = None
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert 'error' in result
        assert result['error'] == 'SendGrid not configured'
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_send_email_api_error(self):
        """Test email sending handles API errors properly"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_client = Mock()
        mock_client.send = Mock(side_effect=Exception('API Error'))
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert 'error' in result
        assert 'API Error' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_email_non_202_status(self):
        """Test email sending with non-success status code"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 400
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='invalid-email',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert result['status_code'] == 400
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_send_template_email_success(self):
        """Test successful template email sending"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_template_email(
            to_email='test@example.com',
            template_id='d-1234567890',
            dynamic_data={'name': 'John', 'order_id': '12345'}
        )
        
        assert result['success'] is True
        assert result['status_code'] == 202
        mock_client.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_template_email_no_client(self):
        """Test template email without configured client"""
        integration = SendGridIntegration()
        integration.client = None
        
        result = await integration.send_template_email(
            to_email='test@example.com',
            template_id='d-123',
            dynamic_data={}
        )
        
        assert 'error' in result
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_send_template_email_error(self):
        """Test template email handles errors"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_client = Mock()
        mock_client.send = Mock(side_effect=Exception('Template not found'))
        integration.client = mock_client
        
        result = await integration.send_template_email(
            to_email='test@example.com',
            template_id='d-invalid',
            dynamic_data={}
        )
        
        assert 'error' in result
        assert 'Template not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_notification_welcome(self):
        """Test sending welcome notification"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='newuser@example.com',
            notification_type='welcome',
            data={'message': 'Welcome aboard!', 'details': 'Get started guide'}
        )
        
        assert result['success'] is True
        mock_client.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_alert(self):
        """Test sending alert notification"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='admin@example.com',
            notification_type='alert',
            data={'message': 'System alert!', 'details': 'High CPU usage detected'}
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_notification_report(self):
        """Test sending report notification"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='user@example.com',
            notification_type='report',
            data={'message': 'Your report is ready'}
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_notification_unknown_type(self):
        """Test notification with unknown type uses default subject"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='test@example.com',
            notification_type='custom_type',
            data={'message': 'Custom notification'}
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_notification_empty_data(self):
        """Test notification with empty data dict"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='test@example.com',
            notification_type='welcome',
            data={}
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_notification_no_client(self):
        """Test notification without configured client"""
        integration = SendGridIntegration()
        integration.client = None
        
        result = await integration.send_notification(
            to_email='test@example.com',
            notification_type='welcome',
            data={'message': 'Test'}
        )
        
        assert 'error' in result
        assert result['test_mode'] is True
    
    def test_module_level_instance(self):
        """Test that module-level instance is created"""
        assert sendgrid_integration is not None
        assert isinstance(sendgrid_integration, SendGridIntegration)
    
    @pytest.mark.asyncio
    async def test_send_email_special_characters(self):
        """Test email with special characters in content"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Test <>&"',
            html_content='<p>Special chars: <>&"€£¥</p>'
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_email_long_content(self):
        """Test email with very long content"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        long_content = '<p>' + 'x' * 10000 + '</p>'
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Long email',
            html_content=long_content
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients_format(self):
        """Test email to single recipient (multiple would be list)"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='user1@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        assert result['success'] is True
        mock_client.send.assert_called_once()


class TestSendGridIntegrationEdgeCases:
    """Edge case tests for SendGrid integration"""
    
    @pytest.mark.asyncio
    async def test_send_email_empty_subject(self):
        """Test email with empty subject"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='',
            html_content='<p>Test</p>'
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_email_empty_html_content(self):
        """Test email with empty HTML content"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content=''
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_template_email_empty_dynamic_data(self):
        """Test template email with empty dynamic data"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_template_email(
            to_email='test@example.com',
            template_id='d-123',
            dynamic_data={}
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_notification_with_html_in_data(self):
        """Test notification with HTML in data fields"""
        integration = SendGridIntegration()
        integration.api_key = 'test_key'
        
        mock_response = Mock()
        mock_response.status_code = 202
        
        mock_client = Mock()
        mock_client.send = Mock(return_value=mock_response)
        integration.client = mock_client
        
        result = await integration.send_notification(
            to_email='test@example.com',
            notification_type='alert',
            data={
                'message': 'Alert <b>with</b> HTML',
                'details': '<script>alert("test")</script>'
            }
        )
        
        assert result['success'] is True