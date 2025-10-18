"""
Unit Tests for Twilio SMS Integration
Tests OTP sending, verification, and SMS functionality
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import os
from backend.integrations.twilio_integration import TwilioIntegration, twilio_integration


class TestTwilioIntegration:
    """Comprehensive test suite for Twilio SMS integration"""
    
    def test_initialization_with_credentials(self):
        """Test Twilio initializes with full credentials"""
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'AC_test_123',
            'TWILIO_AUTH_TOKEN': 'auth_token_456',
            'TWILIO_VERIFY_SERVICE': 'VA_verify_789',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }):
            integration = TwilioIntegration()
            assert integration.account_sid == 'AC_test_123'
            assert integration.auth_token == 'auth_token_456'  # noqa: S105
            assert integration.verify_service_sid == 'VA_verify_789'
            assert integration.client is not None
    
    def test_initialization_without_credentials(self):
        """Test Twilio initializes without client when no credentials"""
        with patch.dict(os.environ, {}, clear=True):
            integration = TwilioIntegration()
            assert integration.account_sid is None
            assert integration.auth_token is None
            assert integration.client is None
    
    def test_initialization_partial_credentials(self):
        """Test initialization with only account SID"""
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'AC_test_123'
        }, clear=True):
            integration = TwilioIntegration()
            assert integration.account_sid == 'AC_test_123'
            assert integration.client is None
    
    @pytest.mark.asyncio
    @patch('backend.integrations.twilio_integration.Client')
    async def test_send_otp_success(self, _mock_client_class):
        """Test successful OTP sending"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        integration.verify_service_sid = 'VA_verify'
        
        # Mock Twilio client
        mock_verification = Mock()
        mock_verification.status = 'pending'
        
        mock_verifications = Mock()
        mock_verifications.create = Mock(return_value=mock_verification)
        
        mock_service = Mock()
        mock_service.verifications = mock_verifications
        
        mock_verify = Mock()
        mock_verify.services = Mock(return_value=mock_service)
        
        mock_client = Mock()
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.send_otp('+971501234567')
        
        assert result['status'] == 'pending'
        assert result['to'] == '+971501234567'
    
    @pytest.mark.asyncio
    async def test_send_otp_not_configured(self):
        """Test OTP sending when Twilio not configured"""
        integration = TwilioIntegration()
        integration.client = None
        
        result = await integration.send_otp('+971501234567')
        
        assert 'error' in result
        assert result['error'] == 'Twilio not configured'
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_send_otp_no_verify_service(self):
        """Test OTP sending without verify service configured"""
        integration = TwilioIntegration()
        integration.client = Mock()
        integration.verify_service_sid = None
        
        result = await integration.send_otp('+971501234567')
        
        assert 'error' in result
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_send_otp_api_error(self):
        """Test OTP sending handles API errors"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        integration.verify_service_sid = 'VA_verify'
        
        mock_client = Mock()
        mock_verify = Mock()
        mock_service = Mock()
        mock_verifications = Mock()
        mock_verifications.create = Mock(side_effect=Exception('Invalid phone number'))
        
        mock_service.verifications = mock_verifications
        mock_verify.services = Mock(return_value=mock_service)
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.send_otp('+invalid')
        
        assert 'error' in result
        assert 'Invalid phone number' in result['error']
    
    @pytest.mark.asyncio
    @patch('backend.integrations.twilio_integration.Client')
    async def test_verify_otp_success(self, _mock_client_class):
        """Test successful OTP verification"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        integration.verify_service_sid = 'VA_verify'
        
        # Mock Twilio client
        mock_check = Mock()
        mock_check.status = 'approved'
        
        mock_checks = Mock()
        mock_checks.create = Mock(return_value=mock_check)
        
        mock_service = Mock()
        mock_service.verification_checks = mock_checks
        
        mock_verify = Mock()
        mock_verify.services = Mock(return_value=mock_service)
        
        mock_client = Mock()
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.verify_otp('+971501234567', '123456')
        
        assert result['valid'] is True
        assert result['status'] == 'approved'
    
    @pytest.mark.asyncio
    async def test_verify_otp_incorrect_code(self):
        """Test OTP verification with incorrect code"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        integration.verify_service_sid = 'VA_verify'
        
        mock_check = Mock()
        mock_check.status = 'pending'
        
        mock_checks = Mock()
        mock_checks.create = Mock(return_value=mock_check)
        
        mock_service = Mock()
        mock_service.verification_checks = mock_checks
        
        mock_verify = Mock()
        mock_verify.services = Mock(return_value=mock_service)
        
        mock_client = Mock()
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.verify_otp('+971501234567', '000000')
        
        assert result['valid'] is False
        assert result['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_verify_otp_not_configured(self):
        """Test OTP verification when Twilio not configured"""
        integration = TwilioIntegration()
        integration.client = None
        
        result = await integration.verify_otp('+971501234567', '123456')
        
        assert result['valid'] is True  # Test mode allows 123456
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_test_mode_wrong_code(self):
        """
        Verify that OTP verification returns invalid when running in test mode with an incorrect code.
        
        Asserts that the verification result has `valid` set to `False` and `test_mode` set to `True`.
        """
        integration = TwilioIntegration()
        integration.client = None
        
        result = await integration.verify_otp('+971501234567', '000000')
        
        assert result['valid'] is False
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_api_error(self):
        """Test OTP verification handles API errors"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        integration.verify_service_sid = 'VA_verify'
        
        mock_client = Mock()
        mock_verify = Mock()
        mock_service = Mock()
        mock_checks = Mock()
        mock_checks.create = Mock(side_effect=Exception('Verification expired'))
        
        mock_service.verification_checks = mock_checks
        mock_verify.services = Mock(return_value=mock_service)
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.verify_otp('+971501234567', '123456')
        
        assert 'error' in result
        assert 'Verification expired' in result['error']
    
    @pytest.mark.asyncio
    @patch('backend.integrations.twilio_integration.Client')
    async def test_send_sms_success(self, _mock_client_class):
        """Test successful SMS sending"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        
        mock_message = Mock()
        mock_message.sid = 'SM123456789'
        mock_message.status = 'queued'
        
        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        
        mock_client = Mock()
        mock_client.messages = mock_messages
        integration.client = mock_client
        
        with patch.dict(os.environ, {'TWILIO_PHONE_NUMBER': '+1234567890'}):
            result = await integration.send_sms(
                to_number='+971501234567',
                message='Test SMS message'
            )
        
        assert result['sid'] == 'SM123456789'
        assert result['status'] == 'queued'
    
    @pytest.mark.asyncio
    async def test_send_sms_with_custom_from_number(self):
        """Test SMS sending with custom from number"""
        integration = TwilioIntegration()
        integration.account_sid = 'AC_test'
        integration.auth_token = 'token'  # noqa: S105
        
        mock_message = Mock()
        mock_message.sid = 'SM_custom'
        mock_message.status = 'sent'
        
        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        
        mock_client = Mock()
        mock_client.messages = mock_messages
        integration.client = mock_client
        
        result = await integration.send_sms(
            to_number='+971501234567',
            message='Custom message',
            from_number='+9999999999'
        )
        
        assert result['sid'] == 'SM_custom'
    
    @pytest.mark.asyncio
    async def test_send_sms_no_client(self):
        """Test SMS sending when client not configured"""
        integration = TwilioIntegration()
        integration.client = None
        
        result = await integration.send_sms(
            to_number='+971501234567',
            message='Test'
        )
        
        assert 'error' in result
        assert result['test_mode'] is True
    
    @pytest.mark.asyncio
    async def test_send_sms_no_from_number(self):
        """Test SMS sending without from number configured"""
        integration = TwilioIntegration()
        integration.client = Mock()
        
        with patch.dict(os.environ, {}, clear=True):
            result = await integration.send_sms(
                to_number='+971501234567',
                message='Test'
            )
        
        assert 'error' in result
        assert 'No Twilio phone number configured' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_sms_api_error(self):
        """Test SMS sending handles API errors"""
        integration = TwilioIntegration()
        integration.client = Mock()
        
        mock_messages = Mock()
        mock_messages.create = Mock(side_effect=Exception('Invalid number'))
        
        integration.client.messages = mock_messages
        
        with patch.dict(os.environ, {'TWILIO_PHONE_NUMBER': '+1234567890'}):
            result = await integration.send_sms(
                to_number='+invalid',
                message='Test'
            )
        
        assert 'error' in result
        assert 'Invalid number' in result['error']
    
    def test_module_level_instance(self):
        """Test module-level instance is created"""
        assert twilio_integration is not None
        assert isinstance(twilio_integration, TwilioIntegration)
    
    @pytest.mark.asyncio
    async def test_send_otp_international_number(self):
        """Test OTP sending to various international numbers"""
        integration = TwilioIntegration()
        integration.client = None  # Test mode
        
        # UAE number
        result = await integration.send_otp('+971501234567')
        assert 'test_mode' in result
        
        # US number
        result = await integration.send_otp('+12125551234')
        assert 'test_mode' in result
    
    @pytest.mark.asyncio
    async def test_send_sms_long_message(self):
        """Test SMS with long message (multi-part)"""
        integration = TwilioIntegration()
        integration.client = Mock()
        
        mock_message = Mock()
        mock_message.sid = 'SM_long'
        mock_message.status = 'queued'
        
        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        
        integration.client.messages = mock_messages
        
        long_message = 'x' * 500  # Long SMS
        
        with patch.dict(os.environ, {'TWILIO_PHONE_NUMBER': '+1234567890'}):
            result = await integration.send_sms(
                to_number='+971501234567',
                message=long_message
            )
        
        assert 'sid' in result
    
    @pytest.mark.asyncio
    async def test_send_sms_special_characters(self):
        """Test SMS with special characters"""
        integration = TwilioIntegration()
        integration.client = Mock()
        
        mock_message = Mock()
        mock_message.sid = 'SM_special'
        mock_message.status = 'sent'
        
        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        
        integration.client.messages = mock_messages
        
        with patch.dict(os.environ, {'TWILIO_PHONE_NUMBER': '+1234567890'}):
            result = await integration.send_sms(
                to_number='+971501234567',
                message='Test with émojis 🎉 and spëcial çhars!'
            )
        
        assert 'sid' in result


class TestTwilioIntegrationEdgeCases:
    """Edge case tests for Twilio integration"""
    
    @pytest.mark.asyncio
    async def test_send_otp_empty_phone_number(self):
        """Test OTP sending with empty phone number"""
        integration = TwilioIntegration()
        integration.client = Mock()
        integration.verify_service_sid = 'VA_test'
        
        mock_client = Mock()
        mock_verify = Mock()
        mock_service = Mock()
        mock_verifications = Mock()
        mock_verifications.create = Mock(side_effect=Exception('Phone number required'))
        
        mock_service.verifications = mock_verifications
        mock_verify.services = Mock(return_value=mock_service)
        mock_client.verify = mock_verify
        integration.client = mock_client
        
        result = await integration.send_otp('')
        
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_verify_otp_empty_code(self):
        """Test OTP verification with empty code"""
        integration = TwilioIntegration()
        integration.client = None
        
        result = await integration.verify_otp('+971501234567', '')
        
        assert result['valid'] is False
    
    @pytest.mark.asyncio
    async def test_send_sms_empty_message(self):
        """Test SMS sending with empty message"""
        integration = TwilioIntegration()
        integration.client = Mock()
        
        mock_messages = Mock()
        mock_messages.create = Mock(side_effect=Exception('Message body required'))
        integration.client.messages = mock_messages
        
        with patch.dict(os.environ, {'TWILIO_PHONE_NUMBER': '+1234567890'}):
            result = await integration.send_sms(
                to_number='+971501234567',
                message=''
            )
        
        assert 'error' in result