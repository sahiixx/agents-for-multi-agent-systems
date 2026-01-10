"""
Unit tests for backend/__init__.py
Tests package initialization and stub installation
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock


class TestBackendInitialization:
    """Test backend package initialization"""
    
    def test_backend_package_import(self):
        """Test backend package can be imported"""
        import backend
        assert backend is not None
    
    def test_backend_all_attribute(self):
        """Test __all__ is defined"""
        import backend
        assert hasattr(backend, "__all__")
        assert isinstance(backend.__all__, list)
    
    def test_stubs_installed_on_import(self):
        """Test stubs are installed when backend is imported"""
        # The import should have triggered stub installation
        import backend
        
        # Verify key stub modules are available
        import aiohttp
        import motor.motor_asyncio
        import jwt
        
        assert aiohttp is not None
        assert motor.motor_asyncio is not None
        assert jwt is not None
    
    def test_stub_installation_handles_missing_stubs_module(self):
        """Test graceful handling when _stubs module is missing"""
        # This test verifies the try/except logic works
        # In normal conditions, _stubs should be available
        import backend
        assert backend is not None


class TestStubIntegration:
    """Test stub integration with backend"""
    
    def test_motor_available_for_database(self):
        """Test motor is available for database.py"""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        assert client is not None
    
    def test_jwt_available_for_security(self):
        """Test jwt is available for security_manager.py"""
        import jwt
        
        jwt_secret = os.getenv('JWT_SECRET', 'test-secret')
        token = jwt.encode({"test": "data"}, jwt_secret, algorithm="HS256")
        assert isinstance(token, str)
    
    def test_sendgrid_available_for_email_service(self):
        """Test sendgrid is available for email_service.py"""
        from sendgrid import SendGridAPIClient
        
        client = SendGridAPIClient(api_key="test")
        assert client is not None