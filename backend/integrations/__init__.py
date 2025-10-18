# Advanced Integrations System
from .crm_integrations import CRMIntegrationManager, crm_manager
from .payment_integrations import PaymentIntegrationManager, payment_manager
# from .communication_integrations import CommunicationIntegrationManager, comm_manager
# from .ecommerce_integrations import EcommerceIntegrationManager, ecommerce_manager

__all__ = [
    'CRMIntegrationManager', 'crm_manager',
    'PaymentIntegrationManager', 'payment_manager', 
    # 'CommunicationIntegrationManager', 'comm_manager',
    # 'EcommerceIntegrationManager', 'ecommerce_manager'
]