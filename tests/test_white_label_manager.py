"""
Comprehensive unit tests for backend/core/white_label_manager.py
Tests multi-tenancy and white-label configuration
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


class TestTenantConfig:
    """Test TenantConfig class"""
    
    def test_tenant_config_creation(self):
        """Test creating TenantConfig with full data"""
        from backend.core.white_label_manager import TenantConfig
        
        data = {
            "tenant_id": "tenant_123",
            "name": "Test Company",
            "domain": "test.company.com",
            "subdomain": "test",
            "branding": {
                "logo_url": "https://example.com/logo.png",
                "primary_color": "#FF0000",
                "secondary_color": "#00FF00",
                "background_color": "#FFFFFF",
                "font_family": "Arial"
            },
            "platform_name": "Test Platform",
            "tagline": "Test Tagline",
            "description": "Test Description",
            "enabled_features": ["feature1", "feature2"],
            "agent_limits": {"max_agents": 10},
            "api_limits": {"requests_per_day": 50000},
            "contact_info": {
                "support_email": "support@test.com",
                "sales_email": "sales@test.com",
                "phone": "+123456789",
                "address": "123 Test St"
            },
            "subscription_tier": "professional",
            "status": "active"
        }
        
        config = TenantConfig(data)
        
        assert config.tenant_id == "tenant_123"
        assert config.name == "Test Company"
        assert config.domain == "test.company.com"
        assert config.primary_color == "#FF0000"
        assert config.platform_name == "Test Platform"
        assert config.subscription_tier == "professional"
    
    def test_tenant_config_with_defaults(self):
        """Test TenantConfig uses defaults for missing fields"""
        from backend.core.white_label_manager import TenantConfig
        
        data = {"name": "Minimal Company"}
        config = TenantConfig(data)
        
        assert config.name == "Minimal Company"
        assert config.primary_color == "#00FF41"
        assert config.platform_name == "AI Business Platform"
        assert config.subscription_tier == "starter"
        assert config.status == "active"
        assert len(config.tenant_id) > 0  # Should generate UUID


class TestWhiteLabelManagerInitialization:
    """Test WhiteLabelManager initialization"""
    
    def test_white_label_manager_creation(self):
        """Test WhiteLabelManager can be created"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        assert manager is not None
        assert isinstance(manager.tenants, dict)
        assert isinstance(manager.domain_mappings, dict)
        assert isinstance(manager.subscription_tiers, dict)
    
    def test_subscription_tiers_defined(self):
        """Test subscription tiers are properly defined"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        assert "starter" in manager.subscription_tiers
        assert "professional" in manager.subscription_tiers
        assert "enterprise" in manager.subscription_tiers
    
    def test_starter_tier_configuration(self):
        """Test starter tier has correct configuration"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        starter = manager.subscription_tiers["starter"]
        
        assert starter["max_agents"] == 3
        assert starter["max_users"] == 10
        assert starter["price"] == 99
        assert "basic_agents" in starter["features"]
    
    def test_professional_tier_configuration(self):
        """Test professional tier has correct configuration"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        pro = manager.subscription_tiers["professional"]
        
        assert pro["max_agents"] == 10
        assert pro["max_users"] == 50
        assert pro["price"] == 299
        assert "white_label" in pro["features"]
    
    def test_enterprise_tier_configuration(self):
        """Test enterprise tier has correct configuration"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        enterprise = manager.subscription_tiers["enterprise"]
        
        assert enterprise["max_agents"] == -1  # unlimited
        assert enterprise["max_users"] == -1  # unlimited
        assert enterprise["price"] == 999
        assert "custom_development" in enterprise["features"]
    
    def test_global_white_label_manager_instance(self):
        """Test global white_label_manager instance exists"""
        from backend.core.white_label_manager import white_label_manager
        
        assert white_label_manager is not None


class TestCreateTenant:
    """Test create_tenant method"""
    
    @pytest.mark.asyncio
    async def test_create_tenant_success(self):
        """Test creating tenant successfully"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        tenant_data = {
            "name": "New Company",
            "domain": "new.company.com",
            "subscription_tier": "professional"
        }
        
        with patch("backend.core.white_label_manager.get_database") as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.tenants = mock_collection
            
            result = await manager.create_tenant(tenant_data)
            
            assert "tenant_id" in result
            assert "domain" in result
            assert result["domain"] == "new.company.com"
    
    @pytest.mark.asyncio
    async def test_create_tenant_with_subdomain(self):
        """Test creating tenant with subdomain"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        tenant_data = {
            "name": "Subdomain Company",
            "subdomain": "mycompany"
        }
        
        with patch("backend.core.white_label_manager.get_database") as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.tenants = mock_collection
            
            result = await manager.create_tenant(tenant_data)
            
            assert "domain" in result
            assert "mycompany" in result["domain"]
    
    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_domain(self):
        """Test creating tenant with duplicate domain returns error"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        # Add existing domain
        manager.domain_mappings["existing.com"] = "tenant_1"
        
        tenant_data = {
            "name": "Duplicate",
            "domain": "existing.com"
        }
        
        result = await manager.create_tenant(tenant_data)
        
        assert "error" in result
        assert "already exists" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_create_tenant_generates_deployment_package(self):
        """Test tenant creation generates deployment package"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        tenant_data = {"name": "Deploy Company"}
        
        with patch("backend.core.white_label_manager.get_database") as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.tenants = mock_collection
            
            with patch.object(manager, "_generate_deployment_package", return_value={"files": []}):
                result = await manager.create_tenant(tenant_data)
                
                assert "deployment_package" in result
                assert "setup_instructions" in result


class TestGetTenantConfig:
    """Test get_tenant_config method"""
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_by_id(self):
        """Test getting tenant config by tenant ID"""
        from backend.core.white_label_manager import WhiteLabelManager, TenantConfig
        
        manager = WhiteLabelManager()
        
        # Add a tenant
        test_config = TenantConfig({"tenant_id": "test_123", "name": "Test"})
        manager.tenants["test_123"] = test_config
        
        config = await manager.get_tenant_config(tenant_id="test_123")
        
        assert config is not None
        assert config.tenant_id == "test_123"
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_by_domain(self):
        """Test getting tenant config by domain"""
        from backend.core.white_label_manager import WhiteLabelManager, TenantConfig
        
        manager = WhiteLabelManager()
        
        # Add tenant with domain mapping
        test_config = TenantConfig({"tenant_id": "test_456", "name": "Test"})
        manager.tenants["test_456"] = test_config
        manager.domain_mappings["test.example.com"] = "test_456"
        
        config = await manager.get_tenant_config(domain="test.example.com")
        
        assert config is not None
        assert config.tenant_id == "test_456"
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_not_found(self):
        """Test getting nonexistent tenant config returns None"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        config = await manager.get_tenant_config(tenant_id="nonexistent")
        
        assert config is None


class TestWhiteLabelManagerIntegration:
    """Integration tests for WhiteLabelManager"""
    
    @pytest.mark.asyncio
    async def test_create_and_retrieve_tenant(self):
        """Test creating and retrieving tenant"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        tenant_data = {
            "name": "Integration Test Company",
            "domain": "integration.test.com"
        }
        
        with patch("backend.core.white_label_manager.get_database") as mock_db:
            mock_collection = AsyncMock()
            mock_db.return_value.tenants = mock_collection
            
            # Create tenant
            result = await manager.create_tenant(tenant_data)
            
            assert "tenant_id" in result
            tenant_id = result["tenant_id"]
            
            # Retrieve tenant
            config = await manager.get_tenant_config(tenant_id=tenant_id)
            assert config is not None
            assert config.tenant_id == tenant_id


class TestSubscriptionTierFeatures:
    """Test subscription tier features"""
    
    def test_all_tiers_have_required_fields(self):
        """Test all subscription tiers have required fields"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        required_fields = ["max_agents", "max_users", "api_requests_per_day", "features", "price"]
        
        for tier_name, tier_config in manager.subscription_tiers.items():
            for field in required_fields:
                assert field in tier_config, f"{tier_name} missing {field}"
    
    def test_tier_pricing_progression(self):
        """Test subscription tiers have progressive pricing"""
        from backend.core.white_label_manager import WhiteLabelManager
        
        manager = WhiteLabelManager()
        
        starter_price = manager.subscription_tiers["starter"]["price"]
        pro_price = manager.subscription_tiers["professional"]["price"]
        enterprise_price = manager.subscription_tiers["enterprise"]["price"]
        
        assert starter_price < pro_price < enterprise_price