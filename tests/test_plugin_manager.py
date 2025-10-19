"""
Comprehensive unit tests for backend/core/plugin_manager.py
Tests plugin system for agent extensions
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from pathlib import Path
import json


class TestPluginInterface:
    """Test PluginInterface abstract base class"""
    
    def test_plugin_interface_cannot_be_instantiated(self):
        """Test PluginInterface cannot be instantiated directly"""
        from backend.core.plugin_manager import PluginInterface
        
        # Should raise TypeError due to abstract methods
        with pytest.raises(TypeError):
            PluginInterface()
    
    def test_plugin_interface_has_required_methods(self):
        """Test PluginInterface defines required abstract methods"""
        from backend.core.plugin_manager import PluginInterface
        
        # Check abstract methods exist
        assert hasattr(PluginInterface, "name")
        assert hasattr(PluginInterface, "version")
        assert hasattr(PluginInterface, "description")
        assert hasattr(PluginInterface, "author")
        assert hasattr(PluginInterface, "capabilities")
        assert hasattr(PluginInterface, "initialize")
        assert hasattr(PluginInterface, "process")
        assert hasattr(PluginInterface, "shutdown")


class TestPluginMetadata:
    """Test PluginMetadata class"""
    
    def test_plugin_metadata_creation(self):
        """Test creating PluginMetadata with full data"""
        from backend.core.plugin_manager import PluginMetadata
        
        data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "license": "MIT",
            "dependencies": ["dep1", "dep2"],
            "capabilities": ["cap1", "cap2"],
            "category": "integration",
            "tags": ["test", "demo"],
            "entry_point": "main.py",
            "config_schema": {"key": "value"}
        }
        
        metadata = PluginMetadata(data)
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
        assert metadata.license == "MIT"
        assert len(metadata.dependencies) == 2
        assert len(metadata.capabilities) == 2
        assert metadata.category == "integration"
    
    def test_plugin_metadata_with_defaults(self):
        """Test PluginMetadata uses defaults for missing fields"""
        from backend.core.plugin_manager import PluginMetadata
        
        data = {"name": "minimal_plugin"}
        metadata = PluginMetadata(data)
        
        assert metadata.name == "minimal_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.license == "MIT"
        assert metadata.category == "general"
        assert isinstance(metadata.dependencies, list)
        assert isinstance(metadata.tags, list)


class TestPluginManagerInitialization:
    """Test PluginManager initialization"""
    
    def test_plugin_manager_creation(self, tmp_path):
        """Test PluginManager can be created"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        assert manager is not None
        assert manager.plugins_directory == plugins_dir
        assert isinstance(manager.loaded_plugins, dict)
        assert isinstance(manager.plugin_metadata, dict)
        assert isinstance(manager.marketplace_plugins, dict)
    
    def test_plugin_manager_has_categories(self):
        """Test PluginManager defines plugin categories"""
        from backend.core.plugin_manager import PluginManager
        
        manager = PluginManager()
        
        assert "integration" in manager.categories
        assert "automation" in manager.categories
        assert "analytics" in manager.categories
        assert "communication" in manager.categories
        assert "security" in manager.categories
        assert "ai" in manager.categories
        assert "custom" in manager.categories
    
    def test_global_plugin_manager_instance(self):
        """Test global plugin_manager instance exists"""
        from backend.core.plugin_manager import plugin_manager
        
        assert plugin_manager is not None


class TestDiscoverPlugins:
    """Test discover_plugins method"""
    
    @pytest.mark.asyncio
    async def test_discover_plugins_empty_directory(self, tmp_path):
        """Test discovering plugins in empty directory"""
        from backend.core.plugin_manager import PluginManager
        
        empty_dir = tmp_path / "empty_plugins"
        manager = PluginManager(plugins_directory=str(empty_dir))
        
        with patch.object(Path, "iterdir", return_value=[]):
            discovered = await manager.discover_plugins()
            assert discovered == []
    
    @pytest.mark.asyncio
    async def test_discover_plugins_with_valid_plugins(self, tmp_path):
        """Test discovering valid plugins"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        # Mock plugin directories with manifests
        mock_plugin1 = MagicMock(spec=Path)
        mock_plugin1.is_dir.return_value = True
        mock_plugin1.name = "plugin1"
        mock_manifest1 = MagicMock(spec=Path)
        mock_manifest1.exists.return_value = True
        mock_plugin1.__truediv__.return_value = mock_manifest1
        
        mock_plugin2 = MagicMock(spec=Path)
        mock_plugin2.is_dir.return_value = True
        mock_plugin2.name = "plugin2"
        mock_manifest2 = MagicMock(spec=Path)
        mock_manifest2.exists.return_value = True
        mock_plugin2.__truediv__.return_value = mock_manifest2
        
        with patch.object(Path, "iterdir", return_value=[mock_plugin1, mock_plugin2]):
            discovered = await manager.discover_plugins()
            
            assert len(discovered) == 2
            assert "plugin1" in discovered
            assert "plugin2" in discovered
    
    @pytest.mark.asyncio
    async def test_discover_plugins_ignores_hidden(self, tmp_path):
        """Test discover_plugins ignores hidden directories"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        mock_hidden = MagicMock(spec=Path)
        mock_hidden.is_dir.return_value = True
        mock_hidden.name = ".hidden"
        
        with patch.object(Path, "iterdir", return_value=[mock_hidden]):
            discovered = await manager.discover_plugins()
            assert len(discovered) == 0


class TestLoadPlugin:
    """Test load_plugin method"""
    
    @pytest.mark.asyncio
    async def test_load_plugin_nonexistent(self, tmp_path):
        """Test loading nonexistent plugin returns False"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        result = await manager.load_plugin("nonexistent_plugin")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_load_plugin_without_manifest(self, tmp_path):
        """Test loading plugin without manifest returns False"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        with patch.object(Path, "exists", side_effect=[True, False]):
            result = await manager.load_plugin("plugin_without_manifest")
            assert result is False


class TestPluginManagerIntegration:
    """Integration tests for PluginManager"""
    
    @pytest.mark.asyncio
    async def test_discover_and_load_workflow(self, tmp_path):
        """Test complete discover and load workflow"""
        from backend.core.plugin_manager import PluginManager
        
        plugins_dir = tmp_path / "test_plugins"
        manager = PluginManager(plugins_directory=str(plugins_dir))
        
        # Discovery should work even with no plugins
        discovered = await manager.discover_plugins()
        assert isinstance(discovered, list)
    
    def test_plugin_categories_comprehensive(self):
        """Test all plugin categories are properly defined"""
        from backend.core.plugin_manager import PluginManager
        
        manager = PluginManager()
        
        expected_categories = [
            "integration",
            "automation",
            "analytics",
            "communication",
            "security",
            "ai",
            "custom"
        ]
        
        for category in expected_categories:
            assert category in manager.categories
            assert isinstance(manager.categories[category], str)
            assert len(manager.categories[category]) > 0


class TestPluginConfiguration:
    """Test plugin configuration management"""
    
    def test_plugin_configs_initialized(self):
        """Test plugin configs dictionary is initialized"""
        from backend.core.plugin_manager import PluginManager
        
        manager = PluginManager()
        assert isinstance(manager.plugin_configs, dict)
    
    def test_marketplace_plugins_initialized(self):
        """Test marketplace plugins dictionary is initialized"""
        from backend.core.plugin_manager import PluginManager
        
        manager = PluginManager()
        assert isinstance(manager.marketplace_plugins, dict)