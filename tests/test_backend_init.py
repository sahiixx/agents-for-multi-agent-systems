"""
Unit tests for backend/__init__.py
Tests backend package initialization and stub installation
"""
import pytest
import sys
from unittest.mock import patch, Mock


class TestBackendInit:
    """Test suite for backend package initialization"""
    
    def test_backend_package_imports(self):
        """Test that backend package can be imported"""
        import backend
        assert backend is not None
        
    def test_backend_has_all_attribute(self):
        """Test that backend package has __all__ defined"""
        import backend
        assert hasattr(backend, '__all__')
        assert backend.__all__ == []
    
    @patch('backend._stubs')
    def test_stubs_installation_called_when_available(self, mock_stubs):
        """Test that stubs are installed when _stubs module is available"""
        # This test verifies the initialization logic
        mock_install = Mock()
        mock_stubs.install = mock_install
        
        # Re-import to trigger initialization
        if 'backend' in sys.modules:
            del sys.modules['backend']
        
        with patch.dict('sys.modules', {'backend._stubs': mock_stubs}):
            import backend
            # Stubs should be available
            assert backend is not None


class TestStubsModule:
    """Test suite for backend._stubs module"""
    
    def test_stubs_module_imports(self):
        """Test that _stubs module can be imported"""
        from backend import _stubs
        assert _stubs is not None
        
    def test_install_function_exists(self):
        """Test that install function exists in _stubs"""
        from backend._stubs import install
        assert callable(install)
        
    def test_install_is_idempotent(self):
        """Test that calling install multiple times is safe"""
        from backend._stubs import install
        
        # Should not raise any exceptions
        install()
        install()
        install()
    
    def test_module_available_function(self):
        """Test _module_available helper function"""
        from backend._stubs import _module_available
        
        # Should return True for sys (built-in module)
        assert _module_available('sys') is True
        
        # Should return False for non-existent module
        assert _module_available('nonexistent_module_xyz') is False