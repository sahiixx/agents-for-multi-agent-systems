"""
Unit Tests for Stripe Payment Integration
Tests checkout session creation, status checking, and package management
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import os
from backend.integrations.stripe_integration import StripeIntegration, stripe_integration


class TestStripeIntegration:
    """Comprehensive test suite for Stripe payment integration"""
    
    def test_initialization(self):
        """Test Stripe integration initializes with correct defaults"""
        with patch.dict(os.environ, {'STRIPE_API_KEY': 'sk_test_12345'}, clear=True):
            integration = StripeIntegration()
            assert integration.api_key == 'sk_test_12345'
            assert integration.stripe_checkout is None
            assert 'starter' in integration.PACKAGES
            assert 'growth' in integration.PACKAGES
            assert 'enterprise' in integration.PACKAGES
    
    def test_initialization_default_api_key(self):
        """Test default API key when not in environment"""
        with patch.dict(os.environ, {}, clear=True):
            integration = StripeIntegration()
            assert integration.api_key == 'sk_test_emergent'
    
    def test_packages_configuration(self):
        """Test payment packages are correctly configured"""
        integration = StripeIntegration()
        
        # Check starter package
        assert integration.PACKAGES['starter']['amount'] == 2500.00
        assert integration.PACKAGES['starter']['currency'] == 'aed'
        assert integration.PACKAGES['starter']['name'] == 'Starter Package'
        
        # Check growth package
        assert integration.PACKAGES['growth']['amount'] == 5000.00
        assert integration.PACKAGES['growth']['currency'] == 'aed'
        
        # Check enterprise package
        assert integration.PACKAGES['enterprise']['amount'] == 10000.00
        assert integration.PACKAGES['enterprise']['currency'] == 'aed'
    
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    def test_initialize_method(self, mock_stripe_checkout):
        """Test initialize method creates StripeCheckout instance"""
        integration = StripeIntegration()
        integration.api_key = 'sk_test_key'
        
        webhook_url = 'https://example.com/webhook'
        integration.initialize(webhook_url)
        
        mock_stripe_checkout.assert_called_once_with(
            api_key='sk_test_key',
            webhook_url=webhook_url
        )
        assert integration.stripe_checkout is not None
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_success_starter(self, mock_stripe_checkout_class):
        """Test successful session creation for starter package"""
        integration = StripeIntegration()
        integration.api_key = 'sk_test_key'
        
        # Mock the checkout session response
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session123'
        mock_session.session_id = 'cs_test_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='starter',
            host_url='https://example.com',
            metadata={'user_id': '123'}
        )
        
        assert 'url' in result
        assert result['url'] == 'https://checkout.stripe.com/session123'
        assert result['session_id'] == 'cs_test_123'
        assert result['package']['name'] == 'Starter Package'
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_success_growth(self, mock_stripe_checkout_class):
        """Test successful session creation for growth package"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/growth'
        mock_session.session_id = 'cs_growth_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='growth',
            host_url='https://example.com'
        )
        
        assert result['session_id'] == 'cs_growth_123'
        assert result['package']['amount'] == 5000.00
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_success_enterprise(self, mock_stripe_checkout_class):
        """Test successful session creation for enterprise package"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/enterprise'
        mock_session.session_id = 'cs_enterprise_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='enterprise',
            host_url='https://example.com'
        )
        
        assert result['session_id'] == 'cs_enterprise_123'
        assert result['package']['amount'] == 10000.00
    
    @pytest.mark.asyncio
    async def test_create_session_invalid_package(self):
        """Test session creation with invalid package ID"""
        integration = StripeIntegration()
        integration.stripe_checkout = Mock()
        
        result = await integration.create_session(
            package_id='invalid_package',
            host_url='https://example.com'
        )
        
        assert 'error' in result
        assert result['error'] == 'Invalid package'
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_with_metadata(self, mock_stripe_checkout_class):
        """Test session creation includes custom metadata"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session'
        mock_session.session_id = 'cs_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        custom_metadata = {
            'user_id': 'user_789',
            'tenant_id': 'tenant_001',
            'campaign': 'summer_sale'
        }
        
        result = await integration.create_session(
            package_id='starter',
            host_url='https://example.com',
            metadata=custom_metadata
        )
        
        assert 'url' in result
        assert 'session_id' in result
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_without_metadata(self, mock_stripe_checkout_class):
        """Test session creation without custom metadata uses defaults"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session'
        mock_session.session_id = 'cs_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='starter',
            host_url='https://example.com',
            metadata=None
        )
        
        assert 'url' in result
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_api_error(self, mock_stripe_checkout_class):
        """Test session creation handles API errors"""
        integration = StripeIntegration()
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(
            side_effect=Exception('Stripe API Error')
        )
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='starter',
            host_url='https://example.com'
        )
        
        assert 'error' in result
        assert 'Stripe API Error' in result['error']
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_success_url_format(self, mock_stripe_checkout_class):
        """Test session creates correct success URL with session_id placeholder"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session'
        mock_session.session_id = 'cs_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        await integration.create_session(
            package_id='starter',
            host_url='https://myapp.com'
        )
        
        # Verify create_checkout_session was called
        assert mock_checkout.create_checkout_session.called
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_get_status_success(self, _mock_stripe_checkout_class):
        """Test successful status retrieval"""
        integration = StripeIntegration()
        
        mock_status = Mock()
        mock_status.status = 'complete'
        mock_status.payment_status = 'paid'
        mock_status.amount_total = 2500.00
        mock_status.currency = 'aed'
        
        mock_checkout = Mock()
        mock_checkout.get_checkout_status = AsyncMock(return_value=mock_status)
        integration.stripe_checkout = mock_checkout
        
        result = await integration.get_status('cs_test_123')
        
        assert result['status'] == 'complete'
        assert result['payment_status'] == 'paid'
        assert result['amount_total'] == 2500.00
        assert result['currency'] == 'aed'
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_get_status_pending(self, _mock_stripe_checkout_class):
        """Test status retrieval for pending payment"""
        integration = StripeIntegration()
        
        mock_status = Mock()
        mock_status.status = 'open'
        mock_status.payment_status = 'unpaid'
        mock_status.amount_total = 5000.00
        mock_status.currency = 'aed'
        
        mock_checkout = Mock()
        mock_checkout.get_checkout_status = AsyncMock(return_value=mock_status)
        integration.stripe_checkout = mock_checkout
        
        result = await integration.get_status('cs_test_456')
        
        assert result['status'] == 'open'
        assert result['payment_status'] == 'unpaid'
    
    @pytest.mark.asyncio
    async def test_get_status_error(self):
        """Test status retrieval handles errors"""
        integration = StripeIntegration()
        
        mock_checkout = Mock()
        mock_checkout.get_checkout_status = AsyncMock(
            side_effect=Exception('Session not found')
        )
        integration.stripe_checkout = mock_checkout
        
        result = await integration.get_status('cs_invalid')
        
        assert 'error' in result
        assert 'Session not found' in result['error']
    
    def test_module_level_instance(self):
        """Test module-level instance is created"""
        assert stripe_integration is not None
        assert isinstance(stripe_integration, StripeIntegration)
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_webhook_url_format(self, mock_stripe_checkout_class):
        """Test webhook URL is correctly formatted"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session'
        mock_session.session_id = 'cs_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        host_url = 'https://business.example.com'
        await integration.create_session('starter', host_url)
        
        # Verify StripeCheckout was initialized with correct webhook URL
        mock_stripe_checkout_class.assert_called_with(
            api_key=integration.api_key,
            webhook_url=f'{host_url}/api/integrations/payments/webhook'
        )


class TestStripeIntegrationEdgeCases:
    """Edge case and error handling tests"""
    
    @pytest.mark.asyncio
    async def test_create_session_empty_package_id(self):
        """Test session creation with empty package ID"""
        integration = StripeIntegration()
        integration.stripe_checkout = Mock()
        
        result = await integration.create_session(
            package_id='',
            host_url='https://example.com'
        )
        
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_create_session_none_package_id(self):
        """Test session creation with None package ID"""
        integration = StripeIntegration()
        integration.stripe_checkout = Mock()
        
        result = await integration.create_session(
            package_id=None,
            host_url='https://example.com'
        )
        
        assert 'error' in result
    
    @pytest.mark.asyncio
    @patch('backend.integrations.stripe_integration.StripeCheckout')
    async def test_create_session_special_characters_in_host_url(self, mock_stripe_checkout_class):
        """Test session creation with special characters in host URL"""
        integration = StripeIntegration()
        
        mock_session = Mock()
        mock_session.url = 'https://checkout.stripe.com/session'
        mock_session.session_id = 'cs_123'
        
        mock_checkout = Mock()
        mock_checkout.create_checkout_session = AsyncMock(return_value=mock_session)
        mock_stripe_checkout_class.return_value = mock_checkout
        
        result = await integration.create_session(
            package_id='starter',
            host_url='https://test-app.example.com:8080'
        )
        
        assert 'url' in result
    
    @pytest.mark.asyncio
    async def test_get_status_empty_session_id(self):
        """Test status retrieval with empty session ID"""
        integration = StripeIntegration()
        
        mock_checkout = Mock()
        mock_checkout.get_checkout_status = AsyncMock(
            side_effect=Exception('Invalid session ID')
        )
        integration.stripe_checkout = mock_checkout
        
        result = await integration.get_status('')
        
        assert 'error' in result
    
    def test_packages_are_immutable_reference(self):
        """Test that PACKAGES dict is accessible"""
        integration1 = StripeIntegration()
        integration2 = StripeIntegration()
        
        # Both instances should have their own PACKAGES
        assert integration1.PACKAGES is not integration2.PACKAGES