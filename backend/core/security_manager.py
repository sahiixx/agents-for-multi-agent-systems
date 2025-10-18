"""
Enterprise Security Manager - Advanced security, RBAC, compliance, and audit logging
Implements enterprise-grade security features for global deployment
"""
import asyncio
import hashlib
import jwt
import logging
import secrets
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import ipaddress
from dataclasses import dataclass

from database import get_database
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    AGENT_MANAGER = "agent_manager"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API_USER = "api_user"

class Permission(Enum):
    # Agent Management
    CREATE_AGENT = "create_agent"
    DELETE_AGENT = "delete_agent"
    CONFIGURE_AGENT = "configure_agent"
    VIEW_AGENT_STATUS = "view_agent_status"
    CONTROL_AGENT = "control_agent"
    
    # Data Access
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    VIEW_INSIGHTS = "view_insights"
    ACCESS_REPORTS = "access_reports"
    
    # System Management
    MANAGE_USERS = "manage_users"
    CONFIGURE_SYSTEM = "configure_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"
    
    # Tenant Management
    CREATE_TENANT = "create_tenant"
    MANAGE_BILLING = "manage_billing"
    WHITE_LABEL_CONFIG = "white_label_config"
    
    # API Access
    API_FULL_ACCESS = "api_full_access"
    API_READ_ONLY = "api_read_only"
    WEBHOOK_MANAGE = "webhook_manage"

class ComplianceStandard(Enum):
    SOC2_TYPE2 = "soc2_type2"
    ISO_27001 = "iso_27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    UAE_DPA = "uae_dpa"  # UAE Data Protection Law

@dataclass
class AuditEvent:
    event_id: str
    user_id: str
    tenant_id: Optional[str]
    action: str
    resource: str
    ip_address: str
    user_agent: str
    timestamp: str
    success: bool
    details: Dict[str, Any]
    risk_level: str  # low, medium, high, critical
    compliance_tags: List[str]

@dataclass
class SecurityPolicy:
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    compliance_standards: List[ComplianceStandard]
    active: bool
    created_at: str
    updated_at: str

class SecurityManager:
    """
    Enterprise Security Manager for NOWHERE Digital Platform
    """
    
    def __init__(self):
        self.ai_service = AIService()
        
        # Security configuration
        self.config = {
            "jwt_secret": secrets.token_urlsafe(32),
            "jwt_expiry_hours": 24,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 30,
            "password_min_length": 12,
            "session_timeout_minutes": 120,
            "api_rate_limits": {
                "default": {"requests": 1000, "window": 3600},  # 1000/hour
                "premium": {"requests": 10000, "window": 3600},  # 10k/hour
                "enterprise": {"requests": 100000, "window": 3600}  # 100k/hour
            }
        }
        
        # Role-based permissions mapping
        self.role_permissions = {
            UserRole.SUPER_ADMIN: [p for p in Permission],  # All permissions
            UserRole.TENANT_ADMIN: [
                Permission.CREATE_AGENT, Permission.CONFIGURE_AGENT, Permission.VIEW_AGENT_STATUS,
                Permission.CONTROL_AGENT, Permission.VIEW_ANALYTICS, Permission.VIEW_INSIGHTS,
                Permission.ACCESS_REPORTS, Permission.MANAGE_USERS, Permission.MANAGE_INTEGRATIONS,
                Permission.API_FULL_ACCESS, Permission.WEBHOOK_MANAGE
            ],
            UserRole.AGENT_MANAGER: [
                Permission.CREATE_AGENT, Permission.CONFIGURE_AGENT, Permission.VIEW_AGENT_STATUS,
                Permission.CONTROL_AGENT, Permission.VIEW_ANALYTICS, Permission.API_READ_ONLY
            ],
            UserRole.ANALYST: [
                Permission.VIEW_AGENT_STATUS, Permission.VIEW_ANALYTICS, Permission.VIEW_INSIGHTS,
                Permission.ACCESS_REPORTS, Permission.EXPORT_DATA
            ],
            UserRole.OPERATOR: [
                Permission.VIEW_AGENT_STATUS, Permission.CONTROL_AGENT, Permission.VIEW_ANALYTICS
            ],
            UserRole.VIEWER: [
                Permission.VIEW_AGENT_STATUS, Permission.VIEW_ANALYTICS
            ],
            UserRole.API_USER: [
                Permission.API_READ_ONLY
            ]
        }
        
        # Security policies
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
        
        # Compliance requirements
        self.compliance_requirements = {
            ComplianceStandard.SOC2_TYPE2: {
                "audit_retention_days": 2555,  # 7 years
                "encryption_required": True,
                "access_reviews_required": True,
                "incident_response_required": True
            },
            ComplianceStandard.GDPR: {
                "data_retention_days": 1095,  # 3 years
                "right_to_erasure": True,
                "consent_management": True,
                "breach_notification_hours": 72
            },
            ComplianceStandard.UAE_DPA: {
                "data_localization": True,
                "consent_required": True,
                "data_retention_days": 730,  # 2 years
                "cross_border_restrictions": True
            }
        }
        
        logger.info("Enterprise Security Manager initialized")
    
    def _get_role_permissions(self, role_str: str) -> List[Permission]:
        """Get permissions for a role string"""
        try:
            # Try to convert string to UserRole enum
            if isinstance(role_str, str):
                for role in UserRole:
                    if role.value == role_str:
                        return self.role_permissions.get(role, [])
            elif isinstance(role_str, UserRole):
                return self.role_permissions.get(role_str, [])
            
            # Default to viewer permissions
            return self.role_permissions.get(UserRole.VIEWER, [])
        except Exception:
            return self.role_permissions.get(UserRole.VIEWER, [])
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with security validation"""
        try:
            # Validate password strength
            password = user_data.get('password', '')
            if not self._validate_password_strength(password):
                return {"error": "Password does not meet security requirements"}
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Generate user ID
            user_id = f"user_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
            
            # Create user record
            user_record = {
                "user_id": user_id,
                "email": user_data.get('email', '').lower(),
                "name": user_data.get('name', ''),
                "role": user_data.get('role', UserRole.VIEWER.value),
                "tenant_id": user_data.get('tenant_id'),
                "password_hash": password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None,
                "active": True,
                "mfa_enabled": False,
                "permissions": [perm.value for perm in self._get_role_permissions(user_data.get('role', UserRole.VIEWER.value))]
            }
            
            # Store in database
            db = get_database()
            await db.users.insert_one(user_record)
            
            # Log audit event
            await self._log_audit_event(AuditEvent(
                event_id=f"user_create_{user_id}",
                user_id="system",
                tenant_id=user_data.get('tenant_id'),
                action="CREATE_USER",
                resource=f"user:{user_id}",
                ip_address=user_data.get('ip_address', '127.0.0.1'),
                user_agent=user_data.get('user_agent', 'System'),
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=True,
                details={"email": user_record["email"], "role": user_record["role"]},
                risk_level="medium",
                compliance_tags=["user_management", "access_control"]
            ))
            
            return {
                "user_id": user_id,
                "email": user_record["email"],
                "role": user_record["role"],
                "permissions": user_record["permissions"]
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {"error": f"Failed to create user: {str(e)}"}
    
    async def authenticate_user(self, email: str, password: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Authenticate user with security checks"""
        try:
            email = email.lower()
            
            # Check for rate limiting
            if self._is_rate_limited(ip_address, "login"):
                await self._log_audit_event(AuditEvent(
                    event_id=f"login_rate_limit_{secrets.token_hex(4)}",
                    user_id=email,
                    tenant_id=None,
                    action="LOGIN_RATE_LIMITED",
                    resource=f"user:{email}",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    success=False,
                    details={"reason": "Rate limit exceeded"},
                    risk_level="high",
                    compliance_tags=["authentication", "security_incident"]
                ))
                return {"error": "Rate limit exceeded. Please try again later."}
            
            # Get user from database
            db = get_database()
            user = await db.users.find_one({"email": email, "active": True})
            
            if not user:
                await self._log_failed_attempt(email, ip_address, "user_not_found")
                return {"error": "Invalid credentials"}
            
            # Verify password
            if not self._verify_password(password, user["password_hash"]):
                await self._log_failed_attempt(email, ip_address, "invalid_password")
                return {"error": "Invalid credentials"}
            
            # Generate JWT token
            token_payload = {
                "user_id": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "tenant_id": user.get("tenant_id"),
                "permissions": [p.value if hasattr(p, 'value') else str(p) for p in user["permissions"]],
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=self.config["jwt_expiry_hours"])
            }
            
            token = jwt.encode(token_payload, self.config["jwt_secret"], algorithm="HS256")
            
            # Update last login
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            self.active_sessions[session_id] = {
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc),
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            # Log successful login
            await self._log_audit_event(AuditEvent(
                event_id=f"login_success_{user['user_id']}",
                user_id=user["user_id"],
                tenant_id=user.get("tenant_id"),
                action="LOGIN_SUCCESS",
                resource=f"user:{user['user_id']}",
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=True,
                details={"login_method": "password"},
                risk_level="low",
                compliance_tags=["authentication"]
            ))
            
            return {
                "token": token,
                "session_id": session_id,
                "user": {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "tenant_id": user.get("tenant_id"),
                    "permissions": token_payload["permissions"]
                },
                "expires_at": token_payload["exp"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"error": "Authentication failed"}
    
    async def validate_permission(self, user_id: str, permission: Permission, resource: str = None) -> bool:
        """Validate user permission for specific action"""
        try:
            db = get_database()
            user = await db.users.find_one({"user_id": user_id, "active": True})
            
            if not user:
                return False
            
            user_permissions = user.get("permissions", [])
            
            # Check if user has the specific permission
            has_permission = any(
                p == permission.value or (hasattr(p, 'value') and p.value == permission.value) 
                for p in user_permissions
            )
            
            # Log permission check
            await self._log_audit_event(AuditEvent(
                event_id=f"permission_check_{user_id}_{secrets.token_hex(4)}",
                user_id=user_id,
                tenant_id=user.get("tenant_id"),
                action="PERMISSION_CHECK",
                resource=resource or "system",
                ip_address="internal",
                user_agent="system",
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=has_permission,
                details={"permission": permission.value, "granted": has_permission},
                risk_level="low",
                compliance_tags=["access_control"]
            ))
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Permission validation error: {e}")
            return False
    
    async def create_security_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new security policy"""
        try:
            policy = SecurityPolicy(
                policy_id=f"policy_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                name=policy_data.get('name', ''),
                description=policy_data.get('description', ''),
                rules=policy_data.get('rules', []),
                compliance_standards=[ComplianceStandard(std) for std in policy_data.get('compliance_standards', [])],
                active=policy_data.get('active', True),
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            
            self.security_policies[policy.policy_id] = policy
            
            # Store in database
            db = get_database()
            await db.security_policies.insert_one({
                "policy_id": policy.policy_id,
                "name": policy.name,
                "description": policy.description,
                "rules": policy.rules,
                "compliance_standards": [std.value for std in policy.compliance_standards],
                "active": policy.active,
                "created_at": policy.created_at,
                "updated_at": policy.updated_at
            })
            
            return {"policy_id": policy.policy_id, "status": "created"}
            
        except Exception as e:
            logger.error(f"Error creating security policy: {e}")
            return {"error": f"Failed to create security policy: {str(e)}"}
    
    async def generate_compliance_report(self, standard: ComplianceStandard, tenant_id: str = None) -> Dict[str, Any]:
        """Generate compliance report for specific standard"""
        try:
            # Get audit events for compliance analysis
            db = get_database()
            
            # Date range for analysis (last 90 days)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=90)
            
            query = {
                "timestamp": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                },
                "compliance_tags": standard.value
            }
            
            if tenant_id:
                query["tenant_id"] = tenant_id
            
            audit_events = await db.audit_logs.find(query).to_list(length=None)
            
            # Analyze compliance metrics
            total_events = len(audit_events)
            security_incidents = len([e for e in audit_events if e.get('risk_level') in ['high', 'critical']])
            failed_access_attempts = len([e for e in audit_events if not e.get('success', True)])
            
            # Generate AI-powered compliance insights
            compliance_prompt = f"""
            Generate a compliance report for {standard.value} standard:
            
            Analysis Period: {start_date.date()} to {end_date.date()}
            Total Audit Events: {total_events}
            Security Incidents: {security_incidents}
            Failed Access Attempts: {failed_access_attempts}
            
            Provide:
            1. Compliance status assessment
            2. Risk areas identification
            3. Recommendations for improvement
            4. Action items for compliance maintenance
            """
            
            ai_analysis = await self.ai_service.generate_content("compliance_analysis", compliance_prompt)
            
            compliance_report = {
                "standard": standard.value,
                "tenant_id": tenant_id,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "metrics": {
                    "total_audit_events": total_events,
                    "security_incidents": security_incidents,
                    "failed_access_attempts": failed_access_attempts,
                    "compliance_score": max(0, 100 - (security_incidents * 5) - (failed_access_attempts * 2))
                },
                "ai_analysis": ai_analysis,
                "recommendations": [
                    "Implement regular security training",
                    "Enhance monitoring and alerting",
                    "Review and update access controls",
                    "Conduct quarterly security assessments"
                ],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": f"Failed to generate compliance report: {str(e)}"}
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < self.config["password_min_length"]:
            return False
        
        # Check for uppercase, lowercase, digits, and special characters
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, stored_password_hash = stored_hash.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == stored_password_hash
        except:
            return False
    
    def _is_rate_limited(self, identifier: str, action: str) -> bool:
        """Check if identifier is rate limited for specific action"""
        # Simple rate limiting implementation
        # In production, use Redis or similar for distributed rate limiting
        current_time = datetime.now(timezone.utc)
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {}
        
        if action not in self.failed_attempts[identifier]:
            self.failed_attempts[identifier][action] = []
        
        # Clean old attempts
        cutoff_time = current_time - timedelta(minutes=60)
        self.failed_attempts[identifier][action] = [
            attempt for attempt in self.failed_attempts[identifier][action]
            if attempt > cutoff_time
        ]
        
        # Check if rate limit exceeded
        return len(self.failed_attempts[identifier][action]) >= self.config["max_login_attempts"]
    
    async def _log_failed_attempt(self, identifier: str, ip_address: str, reason: str):
        """Log failed authentication attempt"""
        current_time = datetime.now(timezone.utc)
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {"login": []}
        
        self.failed_attempts[identifier]["login"].append(current_time)
        
        # Log audit event
        await self._log_audit_event(AuditEvent(
            event_id=f"login_failed_{secrets.token_hex(4)}",
            user_id=identifier,
            tenant_id=None,
            action="LOGIN_FAILED",
            resource=f"user:{identifier}",
            ip_address=ip_address,
            user_agent="unknown",
            timestamp=current_time.isoformat(),
            success=False,
            details={"reason": reason},
            risk_level="medium",
            compliance_tags=["authentication", "security_incident"]
        ))
    
    async def _log_audit_event(self, event: AuditEvent):
        """Log audit event to database"""
        try:
            db = get_database()
            await db.audit_logs.insert_one({
                "event_id": event.event_id,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "action": event.action,
                "resource": event.resource,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "timestamp": event.timestamp,
                "success": event.success,
                "details": event.details,
                "risk_level": event.risk_level,
                "compliance_tags": event.compliance_tags
            })
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

# Global security manager instance
security_manager = SecurityManager()