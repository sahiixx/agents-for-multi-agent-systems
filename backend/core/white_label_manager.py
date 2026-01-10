"""
White Label Manager - Multi-tenancy and branding customization system
Enables resellers and partners to customize the platform with their own branding
"""
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from pathlib import Path

from backend.database import get_database
from backend.models import StandardResponse

logger = logging.getLogger(__name__)

class TenantConfig:
    """Configuration for a white-label tenant"""
    
    def __init__(self, tenant_data: Dict[str, Any]):
        self.tenant_id = tenant_data.get('tenant_id', str(uuid.uuid4()))
        self.name = tenant_data.get('name', '')
        self.domain = tenant_data.get('domain', '')
        self.subdomain = tenant_data.get('subdomain', '')
        
        # Branding configuration
        self.branding = tenant_data.get('branding', {})
        self.logo_url = self.branding.get('logo_url', '')
        self.primary_color = self.branding.get('primary_color', '#00FF41')
        self.secondary_color = self.branding.get('secondary_color', '#00FFFF')
        self.background_color = self.branding.get('background_color', '#000000')
        self.font_family = self.branding.get('font_family', 'Inter')
        
        # Platform configuration
        self.platform_name = tenant_data.get('platform_name', 'AI Business Platform')
        self.tagline = tenant_data.get('tagline', 'AI-Powered Business Automation')
        self.description = tenant_data.get('description', 'Complete AI automation suite')
        
        # Feature configuration
        self.enabled_features = tenant_data.get('enabled_features', [])
        self.agent_limits = tenant_data.get('agent_limits', {'max_agents': 5})
        self.api_limits = tenant_data.get('api_limits', {'requests_per_day': 10000})
        
        # Contact & support
        self.contact_info = tenant_data.get('contact_info', {})
        self.support_email = self.contact_info.get('support_email', '')
        self.sales_email = self.contact_info.get('sales_email', '')
        self.phone = self.contact_info.get('phone', '')
        self.address = self.contact_info.get('address', '')
        
        # Subscription & billing
        self.subscription_tier = tenant_data.get('subscription_tier', 'starter')
        self.billing_info = tenant_data.get('billing_info', {})
        
        # Metadata
        self.created_at = tenant_data.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = tenant_data.get('updated_at', datetime.now(timezone.utc).isoformat())
        self.status = tenant_data.get('status', 'active')

class WhiteLabelManager:
    """
    Manages white-label configurations and multi-tenancy
    """
    
    def __init__(self):
        self.tenants: Dict[str, TenantConfig] = {}
        self.domain_mappings: Dict[str, str] = {}  # domain -> tenant_id
        
        # Subscription tiers and limits
        self.subscription_tiers = {
            "starter": {
                "max_agents": 3,
                "max_users": 10,
                "api_requests_per_day": 5000,
                "features": ["basic_agents", "templates", "support"],
                "price": 99,  # USD per month
                "plugins_limit": 5
            },
            "professional": {
                "max_agents": 10,
                "max_users": 50,
                "api_requests_per_day": 25000,
                "features": ["all_agents", "templates", "plugins", "white_label", "priority_support"],
                "price": 299,
                "plugins_limit": 20
            },
            "enterprise": {
                "max_agents": -1,  # unlimited
                "max_users": -1,   # unlimited  
                "api_requests_per_day": 100000,
                "features": ["all_agents", "templates", "plugins", "white_label", "custom_development", "dedicated_support"],
                "price": 999,
                "plugins_limit": -1  # unlimited
            }
        }
        
        logger.info("White Label Manager initialized")
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new white-label tenant"""
        try:
            tenant_config = TenantConfig(tenant_data)
            
            # Validate domain/subdomain uniqueness
            domain = tenant_config.domain or f"{tenant_config.subdomain}.nowhere.digital"
            if domain in self.domain_mappings:
                return {"error": "Domain already exists"}
            
            # Store tenant configuration
            self.tenants[tenant_config.tenant_id] = tenant_config
            self.domain_mappings[domain] = tenant_config.tenant_id
            
            # Save to database
            db = get_database()
            await db.tenants.insert_one({
                "tenant_id": tenant_config.tenant_id,
                "config": tenant_data,
                "created_at": tenant_config.created_at
            })
            
            # Generate deployment package
            deployment_package = await self._generate_deployment_package(tenant_config)
            
            logger.info(f"Created white-label tenant: {tenant_config.tenant_id}")
            
            return {
                "tenant_id": tenant_config.tenant_id,
                "domain": domain,
                "deployment_package": deployment_package,
                "setup_instructions": self._get_setup_instructions(tenant_config),
                "estimated_setup_time": "2-4 hours"
            }
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            return {"error": f"Failed to create tenant: {str(e)}"}
    
    async def get_tenant_config(self, tenant_id: str = None, domain: str = None) -> Optional[TenantConfig]:
        """Get tenant configuration by ID or domain"""
        if domain and domain in self.domain_mappings:
            tenant_id = self.domain_mappings[domain]
        
        if tenant_id in self.tenants:
            return self.tenants[tenant_id]
        
        # Try loading from database
        if tenant_id:
            db = get_database()
            tenant_doc = await db.tenants.find_one({"tenant_id": tenant_id})
            if tenant_doc:
                config = TenantConfig(tenant_doc.get('config', {}))
                self.tenants[tenant_id] = config
                return config
        
        return None
    
    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update tenant configuration"""
        try:
            tenant = await self.get_tenant_config(tenant_id)
            if not tenant:
                return {"error": "Tenant not found"}
            
            # Update configuration
            current_config = {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "domain": tenant.domain,
                "branding": tenant.branding,
                "platform_name": tenant.platform_name,
                "enabled_features": tenant.enabled_features,
                # ... other fields
            }
            current_config.update(updates)
            current_config["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Create updated tenant config
            updated_tenant = TenantConfig(current_config)
            self.tenants[tenant_id] = updated_tenant
            
            # Update database
            db = get_database()
            await db.tenants.update_one(
                {"tenant_id": tenant_id},
                {"$set": {"config": current_config, "updated_at": current_config["updated_at"]}}
            )
            
            return {"success": True, "message": "Tenant updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating tenant: {e}")
            return {"error": f"Failed to update tenant: {str(e)}"}
    
    async def get_tenant_branding(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant-specific branding configuration"""
        tenant = await self.get_tenant_config(tenant_id)
        if not tenant:
            return self._get_default_branding()
        
        return {
            "platform_name": tenant.platform_name,
            "tagline": tenant.tagline,
            "logo_url": tenant.logo_url,
            "colors": {
                "primary": tenant.primary_color,
                "secondary": tenant.secondary_color,
                "background": tenant.background_color
            },
            "font_family": tenant.font_family,
            "contact_info": {
                "support_email": tenant.support_email,
                "sales_email": tenant.sales_email,
                "phone": tenant.phone,
                "address": tenant.address
            }
        }
    
    async def get_tenant_features(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant-specific feature configuration"""
        tenant = await self.get_tenant_config(tenant_id)
        if not tenant:
            return {"features": [], "limits": {}}
        
        tier_config = self.subscription_tiers.get(tenant.subscription_tier, self.subscription_tiers["starter"])
        
        return {
            "enabled_features": tenant.enabled_features,
            "subscription_tier": tenant.subscription_tier,
            "limits": {
                "max_agents": tier_config["max_agents"],
                "max_users": tier_config["max_users"],
                "api_requests_per_day": tier_config["api_requests_per_day"],
                "plugins_limit": tier_config["plugins_limit"]
            },
            "tier_features": tier_config["features"]
        }
    
    async def validate_tenant_access(self, tenant_id: str, feature: str) -> bool:
        """Validate if tenant has access to a specific feature"""
        tenant = await self.get_tenant_config(tenant_id)
        if not tenant:
            return False
        
        tier_config = self.subscription_tiers.get(tenant.subscription_tier, self.subscription_tiers["starter"])
        return feature in tier_config["features"] or feature in tenant.enabled_features
    
    async def get_all_tenants(self, status: str = None) -> List[Dict[str, Any]]:
        """Get list of all tenants"""
        try:
            db = get_database()
            query = {}
            if status:
                query["config.status"] = status
            
            tenants = []
            async for tenant_doc in db.tenants.find(query):
                config = tenant_doc.get('config', {})
                tenants.append({
                    "tenant_id": config.get('tenant_id'),
                    "name": config.get('name'),
                    "domain": config.get('domain'),
                    "subscription_tier": config.get('subscription_tier', 'starter'),
                    "status": config.get('status', 'active'),
                    "created_at": config.get('created_at')
                })
            
            return tenants
            
        except Exception as e:
            logger.error(f"Error getting tenants: {e}")
            return []
    
    async def create_reseller_package(self, reseller_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a reseller package with custom branding and features"""
        try:
            # Create base tenant configuration for reseller
            tenant_data = {
                "name": reseller_data.get('company_name', ''),
                "domain": reseller_data.get('domain', ''),
                "platform_name": reseller_data.get('platform_name', 'AI Business Platform'),
                "tagline": reseller_data.get('tagline', 'AI-Powered Business Automation'),
                "branding": reseller_data.get('branding', {}),
                "contact_info": reseller_data.get('contact_info', {}),
                "subscription_tier": "enterprise",  # Resellers get enterprise features
                "enabled_features": [
                    "white_label", "reseller_dashboard", "multi_tenant", 
                    "custom_branding", "partner_api", "revenue_sharing"
                ]
            }
            
            tenant_result = await self.create_tenant(tenant_data)
            if "error" in tenant_result:
                return tenant_result
            
            # Generate reseller-specific resources
            reseller_package = {
                "tenant_id": tenant_result["tenant_id"],
                "reseller_dashboard_url": f"https://{tenant_data['domain']}/reseller",
                "api_credentials": {
                    "api_key": f"pk_reseller_{tenant_result['tenant_id'][:8]}",
                    "secret_key": f"sk_reseller_{uuid.uuid4().hex[:16]}"
                },
                "documentation": {
                    "setup_guide": "Complete reseller setup documentation",
                    "api_docs": "Partner API documentation",
                    "branding_guide": "White-label branding guidelines"
                },
                "revenue_sharing": {
                    "commission_rate": reseller_data.get('commission_rate', 20),  # 20% default
                    "payment_terms": "Monthly via bank transfer",
                    "minimum_payout": 1000  # USD
                }
            }
            
            return {
                "success": True,
                "reseller_package": reseller_package,
                "setup_time": "4-8 hours",
                "go_live_estimate": "2-3 business days"
            }
            
        except Exception as e:
            logger.error(f"Error creating reseller package: {e}")
            return {"error": f"Failed to create reseller package: {str(e)}"}
    
    def _get_default_branding(self) -> Dict[str, Any]:
        """Get default NOWHERE branding"""
        return {
            "platform_name": "NOWHERE DIGITAL MEDIA",
            "tagline": "AI-Powered Business Operating System",
            "logo_url": "/assets/logo-matrix.svg",
            "colors": {
                "primary": "#00FF41",
                "secondary": "#00FFFF", 
                "background": "#000000"
            },
            "font_family": "Inter",
            "contact_info": {
                "support_email": "support@nowheredigitalmediai.agency",
                "sales_email": "sales@nowheredigitalmediai.agency",
                "phone": "+971567148469",
                "address": "Boulevard Tower, Downtown Dubai"
            }
        }
    
    async def _generate_deployment_package(self, tenant: TenantConfig) -> Dict[str, Any]:
        """Generate deployment package for tenant"""
        return {
            "docker_compose": "Custom Docker configuration for tenant deployment",
            "environment_variables": {
                "TENANT_ID": tenant.tenant_id,
                "PLATFORM_NAME": tenant.platform_name,
                "PRIMARY_COLOR": tenant.primary_color,
                "DOMAIN": tenant.domain
            },
            "kubernetes_manifests": "Kubernetes deployment manifests",
            "nginx_config": "Custom Nginx configuration for domain routing",
            "database_setup": "Tenant-specific database configuration"
        }
    
    def _get_setup_instructions(self, tenant: TenantConfig) -> List[str]:
        """Get setup instructions for tenant"""
        return [
            "1. Configure DNS to point domain to platform servers",
            "2. Deploy Docker containers with provided configuration",
            "3. Run database migration scripts",
            "4. Upload custom branding assets",
            "5. Configure agent settings and integrations",
            "6. Test all functionality and go live"
        ]

# Global white label manager instance
white_label_manager = WhiteLabelManager()
