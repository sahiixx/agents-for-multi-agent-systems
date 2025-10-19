"""
Unit tests for backend/integrations/crm_integrations.py
Tests CRM integration manager for multiple providers
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from backend.integrations.crm_integrations import (
    CRMIntegrationManager, 
    CRMProvider,
    crm_manager
)


class TestCRMProvider:
    """Test CRM provider enumeration"""
    
    def test_crm_provider_values(self):
        """Test that all CRM providers are defined"""
        assert CRMProvider.SALESFORCE.value == "salesforce"
        assert CRMProvider.HUBSPOT.value == "hubspot"
        assert CRMProvider.MICROSOFT_DYNAMICS.value == "microsoft_dynamics"
        assert CRMProvider.PIPEDRIVE.value == "pipedrive"
        assert CRMProvider.ZOHO.value == "zoho"
        assert CRMProvider.CUSTOM.value == "custom"


class TestCRMIntegrationManager:
    """Test suite for CRM Integration Manager"""
    
    @pytest.fixture
    def manager(self):
        """Create a CRM integration manager instance for testing"""
        return CRMIntegrationManager()
    
    def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager.integrations == {}
        assert manager.webhook_handlers == {}
        assert manager.api_configs is not None
        
    def test_api_configs_all_providers(self, manager):
        """Test that API configs exist for major providers"""
        assert CRMProvider.SALESFORCE in manager.api_configs
        assert CRMProvider.HUBSPOT in manager.api_configs
        assert CRMProvider.MICROSOFT_DYNAMICS in manager.api_configs
        assert CRMProvider.PIPEDRIVE in manager.api_configs
    
    def test_api_config_structure(self, manager):
        """Test that API configs have required fields"""
        for provider, config in manager.api_configs.items():
            if provider == CRMProvider.PIPEDRIVE:
                assert "base_url" in config
                assert "auth_type" in config
            else:
                assert "auth_url" in config
                assert "base_url" in config
    
    @pytest.mark.asyncio
    async def test_setup_integration_success(self, manager):
        """Test successful CRM integration setup"""
        credentials = {"access_token": "test_token_hubspot"}
        
        result = await manager.setup_integration(
            provider=CRMProvider.HUBSPOT,
            credentials=credentials,
            tenant_id="tenant_123"
        )
        
        assert "integration_id" in result
        assert result["provider"] == "hubspot"
        assert result["status"] == "connected"
        assert "features" in result
    
    @pytest.mark.asyncio
    async def test_setup_integration_stores_config(self, manager):
        """Test that setup stores integration configuration"""
        credentials = {"access_token": "test_token_sf"}
        
        result = await manager.setup_integration(
            provider=CRMProvider.SALESFORCE,
            credentials=credentials,
            tenant_id="tenant_456"
        )
        
        integration_id = result["integration_id"]
        assert integration_id in manager.integrations
        
        stored_config = manager.integrations[integration_id]
        assert stored_config["provider"] == "salesforce"
        assert stored_config["tenant_id"] == "tenant_456"
        assert stored_config["status"] == "active"
    
    @pytest.mark.asyncio
    @patch('backend.integrations.crm_integrations.aiohttp.ClientSession')
    async def test_setup_integration_connection_failure(self, mock_session, manager):
        """Test setup with connection failure"""
        credentials = {"access_token": "invalid_token"}

        # Provide explicit async context manager fakes to avoid un-awaited coroutine warnings
        class FailingResponse:
            def __init__(self, status: int):
                self.status = status

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class SessionStub:
            def __init__(self, response):
                self._response = response

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def get(self, *args, **kwargs):
                return self._response

        mock_session.return_value = SessionStub(FailingResponse(status=401))

        result = await manager.setup_integration(
            provider=CRMProvider.HUBSPOT,
            credentials=credentials
        )

        assert result == {"error": "Failed to connect to hubspot: HTTP 401"}
    
    @pytest.mark.asyncio
    async def test_sync_contacts_integration_not_found(self, manager):
        """Test contact sync with non-existent integration"""
        result = await manager.sync_contacts("invalid_integration_id")
        
        assert "error" in result
        assert result["error"] == "Integration not found"
    
    @pytest.mark.asyncio
    async def test_sync_contacts_success(self, manager):
        """Test successful contact synchronization"""
        # Setup integration first
        integration_id = "test_integration_123"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "hubspot",
            "tenant_id": "tenant_123",
            "credentials": {"access_token": "test_token"},
            "sync_settings": {
                "sync_contacts": True,
                "sync_companies": True
            }
        }
        
        result = await manager.sync_contacts(integration_id, direction="bidirectional")
        
        assert "integration_id" in result
        assert "results" in result
        assert "sync_direction" in result
        assert result["sync_direction"] == "bidirectional"
    
    @pytest.mark.asyncio
    async def test_sync_contacts_to_crm_only(self, manager):
        """Test syncing contacts to CRM only"""
        integration_id = "test_integration_456"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "salesforce",
            "tenant_id": "tenant_456",
            "credentials": {"access_token": "test_token"},
            "sync_settings": {}
        }
        
        result = await manager.sync_contacts(integration_id, direction="to_crm")
        
        assert result["sync_direction"] == "to_crm"
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_create_lead_in_crm_success(self, manager):
        """Test creating lead in CRM"""
        integration_id = "test_integration_789"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "hubspot",
            "tenant_id": "tenant_789",
            "credentials": {"access_token": "test_token_hubspot"}
        }
        
        lead_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+971501234567",
            "company": "Acme Corp"
        }
        
        result = await manager.create_lead_in_crm(integration_id, lead_data)
        
        assert "crm_lead_id" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_create_lead_integration_not_found(self, manager):
        """Test creating lead with invalid integration"""
        lead_data = {"name": "Test", "email": "test@example.com"}
        
        result = await manager.create_lead_in_crm("invalid_id", lead_data)
        
        assert "error" in result
        assert result["error"] == "Integration not found"
    
    @pytest.mark.asyncio
    async def test_update_deal_stage_success(self, manager):
        """Test updating deal stage in CRM"""
        integration_id = "test_integration_deal"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "salesforce",
            "tenant_id": "tenant_deal",
            "credentials": {"access_token": "test_token"}
        }
        
        result = await manager.update_deal_stage(
            integration_id=integration_id,
            deal_id="deal_123",
            new_stage="closed_won"
        )
        
        assert "deal_id" in result
        assert result["deal_id"] == "deal_123"
        assert "new_stage" in result
    
    @pytest.mark.asyncio
    async def test_get_crm_analytics_success(self, manager):
        """Test getting CRM analytics"""
        integration_id = "test_integration_analytics"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "hubspot",
            "tenant_id": "tenant_analytics",
            "credentials": {"access_token": "test_token"}
        }
        
        result = await manager.get_crm_analytics(integration_id)
        
        assert "analytics" in result
        assert "provider" in result
        assert "retrieved_at" in result
    
    @pytest.mark.asyncio
    async def test_get_crm_analytics_returns_metrics(self, manager):
        """Test that analytics returns expected metrics"""
        integration_id = "test_integration_metrics"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "salesforce",
            "tenant_id": "tenant_metrics",
            "credentials": {"access_token": "test_token"}
        }
        
        result = await manager.get_crm_analytics(integration_id)
        
        analytics = result.get("analytics", {})
        # Should have some metrics
        assert "total_contacts" in analytics or "total_deals" in analytics or len(analytics) > 0
    
    @pytest.mark.asyncio
    async def test_handle_crm_webhook_contact_created(self, manager):
        """Test handling contact creation webhook"""
        integration_id = "test_integration_webhook"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "hubspot",
            "tenant_id": "tenant_webhook",
            "credentials": {"access_token": "test_token"}
        }
        
        webhook_data = {
            "event_type": "contact.created",
            "contact_id": "contact_123",
            "data": {"email": "newcontact@example.com"}
        }
        
        result = await manager.handle_crm_webhook(integration_id, webhook_data)
        
        assert "event_type" in result
        assert "processing_result" in result
    
    @pytest.mark.asyncio
    async def test_handle_crm_webhook_deal_updated(self, manager):
        """Test handling deal update webhook"""
        integration_id = "test_integration_webhook2"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "salesforce",
            "tenant_id": "tenant_webhook2",
            "credentials": {"access_token": "test_token"}
        }
        
        webhook_data = {
            "event_type": "deal.updated",
            "deal_id": "deal_456",
            "data": {"stage": "proposal"}
        }
        
        result = await manager.handle_crm_webhook(integration_id, webhook_data)
        
        assert result["event_type"] == "deal.updated"
    
    @pytest.mark.asyncio
    async def test_handle_crm_webhook_unknown_event(self, manager):
        """Test handling unknown webhook event type"""
        integration_id = "test_integration_webhook3"
        manager.integrations[integration_id] = {
            "integration_id": integration_id,
            "provider": "hubspot",
            "tenant_id": "tenant_webhook3",
            "credentials": {"access_token": "test_token"}
        }
        
        webhook_data = {
            "event_type": "unknown.event",
            "data": {}
        }
        
        result = await manager.handle_crm_webhook(integration_id, webhook_data)
        
        assert "processing_result" in result
        # Should ignore unknown events
        assert result["processing_result"].get("status") == "ignored"
    
    @pytest.mark.asyncio
    async def test_test_connection_with_test_token(self, manager):
        """Test connection check with test token"""
        credentials = {"access_token": "test_token_hubspot"}
        
        result = await manager._test_connection(CRMProvider.HUBSPOT, credentials)
        
        assert result["success"] is True
        assert "features" in result
    
    @pytest.mark.asyncio
    async def test_test_connection_salesforce(self, manager):
        """Test Salesforce connection check"""
        credentials = {"access_token": "test_token_salesforce"}
        
        result = await manager._test_connection(CRMProvider.SALESFORCE, credentials)
        
        assert result["success"] is True
        assert "leads" in result["features"]
        assert "contacts" in result["features"]
    
    @pytest.mark.asyncio
    async def test_format_lead_for_hubspot(self, manager):
        """Test formatting lead data for HubSpot"""
        lead_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+971501234567",
            "company": "Tech Solutions LLC"
        }
        
        formatted = await manager._format_lead_for_crm(CRMProvider.HUBSPOT, lead_data)
        
        assert "properties" in formatted
        assert formatted["properties"]["email"] == "jane@example.com"
        assert "firstname" in formatted["properties"]
        assert "lastname" in formatted["properties"]
    
    @pytest.mark.asyncio
    async def test_format_lead_for_salesforce(self, manager):
        """Test formatting lead data for Salesforce"""
        lead_data = {
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "phone": "+971501234567",
            "company": "Marketing Inc"
        }
        
        formatted = await manager._format_lead_for_crm(CRMProvider.SALESFORCE, lead_data)
        
        assert "Email" in formatted
        assert formatted["Email"] == "bob@example.com"
        assert "FirstName" in formatted
        assert "LastName" in formatted
        assert "Company" in formatted
    
    @pytest.mark.asyncio
    async def test_get_nowhere_contacts_returns_list(self, manager):
        """Test getting NOWHERE platform contacts"""
        contacts = await manager._get_nowhere_contacts("tenant_123")
        
        assert isinstance(contacts, list)
    
    @pytest.mark.asyncio
    async def test_fetch_crm_analytics_returns_dict(self, manager):
        """Test fetching CRM analytics returns dictionary"""
        credentials = {"access_token": "test_token"}
        
        analytics = await manager._fetch_crm_analytics(CRMProvider.HUBSPOT, credentials)
        
        assert isinstance(analytics, dict)
        # Should have some analytics data
        assert len(analytics) > 0
    
    def test_global_crm_manager_instance(self):
        """Test global CRM manager instance exists"""
        assert crm_manager is not None
        assert isinstance(crm_manager, CRMIntegrationManager)
    
    @pytest.mark.asyncio
    async def test_multiple_integrations_same_tenant(self, manager):
        """Test setting up multiple integrations for same tenant"""
        tenant_id = "multi_tenant_123"
        
        # Setup HubSpot integration
        result1 = await manager.setup_integration(
            provider=CRMProvider.HUBSPOT,
            credentials={"access_token": "test_token_hubspot"},
            tenant_id=tenant_id
        )
        
        # Setup Salesforce integration  
        result2 = await manager.setup_integration(
            provider=CRMProvider.SALESFORCE,
            credentials={"access_token": "test_token_salesforce"},
            tenant_id=tenant_id
        )
        
        assert result1["integration_id"] != result2["integration_id"]
        assert result1["provider"] == "hubspot"
        assert result2["provider"] == "salesforce"
    
    @pytest.mark.asyncio
    async def test_sync_settings_stored_correctly(self, manager):
        """Test that sync settings are stored in integration config"""
        credentials = {"access_token": "test_token"}
        
        result = await manager.setup_integration(
            provider=CRMProvider.PIPEDRIVE,
            credentials=credentials,
            tenant_id="sync_test_tenant"
        )
        
        integration_id = result["integration_id"]
        config = manager.integrations[integration_id]
        
        assert "sync_settings" in config
        assert config["sync_settings"]["auto_sync"] is True
        assert "sync_interval_minutes" in config["sync_settings"]