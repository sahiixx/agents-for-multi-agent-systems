"""
Plugin Manager - Core system for managing agent plugins and extensions
Implements the modular plugin architecture for extensibility
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timezone
from pathlib import Path
import importlib
import inspect
from abc import ABC, abstractmethod

from backend.agents.base_agent import BaseAgent, AgentCapability

logger = logging.getLogger(__name__)

class PluginInterface(ABC):
    """
    Base interface that all plugins must implement
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description"""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """Plugin author"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Plugin capabilities"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the plugin"""
        pass

class PluginMetadata:
    """Plugin metadata container"""
    
    def __init__(self, plugin_data: Dict[str, Any]):
        self.name = plugin_data.get('name', '')
        self.version = plugin_data.get('version', '1.0.0')
        self.description = plugin_data.get('description', '')
        self.author = plugin_data.get('author', '')
        self.license = plugin_data.get('license', 'MIT')
        self.dependencies = plugin_data.get('dependencies', [])
        self.capabilities = plugin_data.get('capabilities', [])
        self.category = plugin_data.get('category', 'general')
        self.tags = plugin_data.get('tags', [])
        self.entry_point = plugin_data.get('entry_point', 'plugin.py')
        self.config_schema = plugin_data.get('config_schema', {})
        self.created_at = plugin_data.get('created_at', datetime.now(timezone.utc).isoformat())

class PluginManager:
    """
    Central plugin manager for the NOWHERE platform
    Handles plugin discovery, loading, lifecycle management
    """
    
    def __init__(self, plugins_directory: str = "/app/plugins"):
        self.plugins_directory = Path(plugins_directory)
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Plugin registry for marketplace
        self.marketplace_plugins: Dict[str, Dict[str, Any]] = {}
        
        # Plugin categories
        self.categories = {
            "integration": "External service integrations",
            "automation": "Workflow and process automation", 
            "analytics": "Data analysis and reporting",
            "communication": "Client and team communication",
            "security": "Security and compliance tools",
            "ai": "AI and machine learning extensions",
            "custom": "Custom business logic plugins"
        }
        
        # Ensure plugins directory exists
        self.plugins_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Plugin Manager initialized with directory: {self.plugins_directory}")
    
    async def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugins directory"""
        discovered = []
        
        try:
            for plugin_dir in self.plugins_directory.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                    plugin_manifest = plugin_dir / 'manifest.json'
                    if plugin_manifest.exists():
                        discovered.append(plugin_dir.name)
                        logger.info(f"Discovered plugin: {plugin_dir.name}")
            
            return discovered
            
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")
            return []
    
    async def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """Load a specific plugin"""
        try:
            plugin_path = self.plugins_directory / plugin_name
            
            if not plugin_path.exists():
                logger.error(f"Plugin directory not found: {plugin_name}")
                return False
            
            # Load plugin metadata
            manifest_path = plugin_path / 'manifest.json'
            if not manifest_path.exists():
                logger.error(f"Plugin manifest not found: {plugin_name}")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            metadata = PluginMetadata(manifest_data)
            self.plugin_metadata[plugin_name] = metadata
            
            # Check dependencies
            if not await self._check_dependencies(metadata.dependencies):
                logger.error(f"Plugin dependencies not met: {plugin_name}")
                return False
            
            # Load plugin code
            plugin_module_path = plugin_path / metadata.entry_point
            if not plugin_module_path.exists():
                logger.error(f"Plugin entry point not found: {plugin_name}")
                return False
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", 
                plugin_module_path
            )
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(plugin_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"Plugin class not found: {plugin_name}")
                return False
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            
            # Initialize plugin
            plugin_config = config or self.plugin_configs.get(plugin_name, {})
            if await plugin_instance.initialize(plugin_config):
                self.loaded_plugins[plugin_name] = plugin_instance
                self.plugin_configs[plugin_name] = plugin_config
                logger.info(f"Plugin loaded successfully: {plugin_name}")
                return True
            else:
                logger.error(f"Plugin initialization failed: {plugin_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        try:
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                await plugin.shutdown()
                del self.loaded_plugins[plugin_name]
                logger.info(f"Plugin unloaded: {plugin_name}")
                return True
            else:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def execute_plugin_task(self, plugin_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using a specific plugin"""
        try:
            if plugin_name not in self.loaded_plugins:
                return {"error": f"Plugin not loaded: {plugin_name}"}
            
            plugin = self.loaded_plugins[plugin_name]
            result = await plugin.process(task)
            
            return {
                "success": True,
                "plugin": plugin_name,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Plugin task execution failed {plugin_name}: {e}")
            return {"error": f"Plugin execution failed: {str(e)}"}
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins"""
        discovered = await self.discover_plugins()
        results = {}
        
        for plugin_name in discovered:
            results[plugin_name] = await self.load_plugin(plugin_name)
        
        return results
    
    async def get_plugin_info(self, plugin_name: str = None) -> Dict[str, Any]:
        """Get information about plugins"""
        if plugin_name:
            if plugin_name in self.plugin_metadata:
                metadata = self.plugin_metadata[plugin_name]
                is_loaded = plugin_name in self.loaded_plugins
                
                return {
                    "name": metadata.name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author,
                    "license": metadata.license,
                    "category": metadata.category,
                    "capabilities": metadata.capabilities,
                    "is_loaded": is_loaded,
                    "dependencies": metadata.dependencies
                }
            else:
                return {"error": f"Plugin not found: {plugin_name}"}
        
        # Return info for all plugins
        all_plugins = {}
        for name, metadata in self.plugin_metadata.items():
            is_loaded = name in self.loaded_plugins
            all_plugins[name] = {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "category": metadata.category,
                "is_loaded": is_loaded
            }
        
        return {
            "total_plugins": len(all_plugins),
            "loaded_plugins": len(self.loaded_plugins),
            "categories": self.categories,
            "plugins": all_plugins
        }
    
    async def install_plugin_from_marketplace(self, plugin_id: str, source: str) -> Dict[str, Any]:
        """Install a plugin from marketplace or URL"""
        try:
            # This would integrate with plugin marketplace/repository
            # For now, return placeholder implementation
            
            return {
                "plugin_id": plugin_id,
                "status": "installation_queued",
                "message": f"Plugin {plugin_id} installation initiated",
                "estimated_time": "2-5 minutes"
            }
            
        except Exception as e:
            logger.error(f"Plugin installation failed: {e}")
            return {"error": f"Installation failed: {str(e)}"}
    
    async def create_plugin_template(self, plugin_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plugin template for development"""
        try:
            plugin_name = plugin_info.get('name', 'my_plugin')
            plugin_dir = self.plugins_directory / plugin_name
            
            # Create plugin directory
            plugin_dir.mkdir(exist_ok=True)
            
            # Create manifest.json
            manifest = {
                "name": plugin_info.get('name', 'My Plugin'),
                "version": plugin_info.get('version', '1.0.0'),
                "description": plugin_info.get('description', 'Custom plugin'),
                "author": plugin_info.get('author', 'Plugin Developer'),
                "license": plugin_info.get('license', 'MIT'),
                "category": plugin_info.get('category', 'custom'),
                "capabilities": plugin_info.get('capabilities', []),
                "dependencies": [],
                "entry_point": "plugin.py",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            with open(plugin_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create plugin.py template
            plugin_template = f'''"""
{manifest['name']} - Custom Plugin
{manifest['description']}
"""
from typing import Dict, Any, List
from backend.core.plugin_manager import PluginInterface
from backend.agents.base_agent import AgentCapability

class {plugin_name.replace('_', '').title()}Plugin(PluginInterface):
    """
    Custom plugin implementation
    """
    
    @property
    def name(self) -> str:
        return "{manifest['name']}"
    
    @property
    def version(self) -> str:
        return "{manifest['version']}"
    
    @property
    def description(self) -> str:
        return "{manifest['description']}"
    
    @property
    def author(self) -> str:
        return "{manifest['author']}"
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return []  # Add your capabilities here
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        try:
            # Add your initialization logic here
            return True
        except Exception as e:
            print(f"Plugin initialization failed: {{e}}")
            return False
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task"""
        try:
            # Add your task processing logic here
            return {{
                "message": f"Task processed by {manifest['name']}",
                "task_id": task.get('id', 'unknown'),
                "result": "success"
            }}
        except Exception as e:
            return {{"error": f"Task processing failed: {{str(e)}}"}}
    
    async def shutdown(self) -> bool:
        """Shutdown the plugin"""
        try:
            # Add your cleanup logic here
            return True
        except Exception as e:
            print(f"Plugin shutdown failed: {{e}}")
            return False
'''
            
            with open(plugin_dir / 'plugin.py', 'w') as f:
                f.write(plugin_template)
            
            # Create README.md
            readme_content = f"""# {manifest['name']}

{manifest['description']}

## Installation

1. Place this plugin directory in the plugins folder
2. Configure the plugin in your agent system
3. Load the plugin via the Plugin Manager

## Configuration

Add any configuration options here.

## Usage

Describe how to use your plugin.

## Author

{manifest['author']}

## License

{manifest['license']}
"""
            
            with open(plugin_dir / 'README.md', 'w') as f:
                f.write(readme_content)
            
            return {
                "plugin_name": plugin_name,
                "plugin_path": str(plugin_dir),
                "files_created": ["manifest.json", "plugin.py", "README.md"],
                "message": f"Plugin template created successfully at {plugin_dir}"
            }
            
        except Exception as e:
            logger.error(f"Plugin template creation failed: {e}")
            return {"error": f"Template creation failed: {str(e)}"}
    
    async def validate_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Validate a plugin's structure and compatibility"""
        try:
            plugin_path = self.plugins_directory / plugin_name
            
            validation_results = {
                "plugin_name": plugin_name,
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Check if plugin directory exists
            if not plugin_path.exists():
                validation_results["valid"] = False
                validation_results["issues"].append("Plugin directory not found")
                return validation_results
            
            # Check manifest.json
            manifest_path = plugin_path / 'manifest.json'
            if not manifest_path.exists():
                validation_results["valid"] = False
                validation_results["issues"].append("manifest.json not found")
            else:
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        
                    required_fields = ['name', 'version', 'description', 'author', 'entry_point']
                    for field in required_fields:
                        if field not in manifest:
                            validation_results["issues"].append(f"Missing required field in manifest: {field}")
                            validation_results["valid"] = False
                            
                except json.JSONDecodeError:
                    validation_results["valid"] = False
                    validation_results["issues"].append("Invalid JSON in manifest.json")
            
            # Check entry point file
            if "valid" in validation_results and validation_results["valid"]:
                entry_point = manifest.get('entry_point', 'plugin.py')
                entry_path = plugin_path / entry_point
                
                if not entry_path.exists():
                    validation_results["valid"] = False
                    validation_results["issues"].append(f"Entry point file not found: {entry_point}")
            
            # Additional validation checks can be added here
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            return {
                "plugin_name": plugin_name,
                "valid": False,
                "error": str(e)
            }
    
    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if plugin dependencies are met"""
        # For now, return True. In production, this would check:
        # - Python package dependencies
        # - System dependencies  
        # - Other plugin dependencies
        # - API availability
        return True
    
    async def get_marketplace_plugins(self) -> Dict[str, Any]:
        """Get available plugins from marketplace"""
        # Mock marketplace data - in production this would fetch from actual marketplace
        return {
            "featured_plugins": [
                {
                    "id": "hubspot_integration",
                    "name": "HubSpot CRM Integration",
                    "description": "Seamless integration with HubSpot CRM system",
                    "category": "integration",
                    "rating": 4.8,
                    "downloads": 1250,
                    "price": "Free"
                },
                {
                    "id": "stripe_payments", 
                    "name": "Stripe Payment Processing",
                    "description": "Accept payments through Stripe integration",
                    "category": "integration",
                    "rating": 4.9,
                    "downloads": 2100,
                    "price": "$29/month"
                },
                {
                    "id": "social_media_automation",
                    "name": "Social Media Automation",
                    "description": "Automate social media posting and engagement",
                    "category": "automation", 
                    "rating": 4.6,
                    "downloads": 890,
                    "price": "$19/month"
                }
            ],
            "categories": self.categories,
            "total_available": 47
        }

# Global plugin manager instance
plugin_manager = PluginManager()
