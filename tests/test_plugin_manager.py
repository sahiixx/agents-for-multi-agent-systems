"""
Unit tests for backend/core/plugin_manager.py
Covers discovery, load/unload, execution, metadata, validation.
"""
import json
import pytest
from pathlib import Path
from backend.core.plugin_manager import PluginManager, PluginInterface, AgentCapability

PLUGIN_CODE = '''from typing import Dict, Any, List
from backend.core.plugin_manager import PluginInterface
from backend.agents.base_agent import AgentCapability

class ExamplePlugin(PluginInterface):
    @property
    def name(self) -> str: return "Example Plugin"
    @property
    def version(self) -> str: return "1.0.0"
    @property
    def description(self) -> str: return "Example plugin for tests"
    @property
    def author(self) -> str: return "Tester"
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.DATA_ANALYSIS]

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self._inited = True
        self._config = config
        return True

    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"echo": task, "ok": True}

    async def shutdown(self) -> bool:
        self._inited = False
        return True
'''

@pytest.mark.asyncio
async def test_plugin_discovery_load_execute_unload(tmp_path: Path):
    # Arrange: create a plugin folder
    plugin_root = tmp_path / "plugins"
    plugin_dir = plugin_root / "example_plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.py").write_text(PLUGIN_CODE)
    (plugin_dir / "manifest.json").write_text(json.dumps({
        "name": "Example Plugin",
        "version": "1.0.0",
        "description": "Example plugin for tests",
        "author": "Tester",
        "entry_point": "plugin.py",
        "category": "ai",
        "capabilities": ["data_analysis"]
    }, indent=2))

    mgr = PluginManager(str(plugin_root))
    discovered = await mgr.discover_plugins()
    assert "example_plugin" in discovered

    loaded = await mgr.load_plugin("example_plugin", config={"x": 1})
    assert loaded is True
    exec_res = await mgr.execute_plugin_task("example_plugin", {"id": "t1"})
    assert exec_res["success"] is True and exec_res["plugin"] == "example_plugin"

    # Info and validation
    info = await mgr.get_plugin_info("example_plugin")
    assert info["name"] == "Example Plugin"
    val = await mgr.validate_plugin("example_plugin")
    assert val["valid"] is True

    # Unload
    ok = await mgr.unload_plugin("example_plugin")
    assert ok is True

@pytest.mark.asyncio
async def test_load_all_plugins_and_marketplace_listing(tmp_path: Path):
    plugin_root = tmp_path / "p2"
    plugin_root.mkdir()
    # Two plugins
    for p in ("pA", "pB"):
        d = plugin_root / p
        d.mkdir()
        (d / "plugin.py").write_text(PLUGIN_CODE.replace("ExamplePlugin", f"{p}Plugin"))
        (d / "manifest.json").write_text(json.dumps({
            "name": p,
            "version": "0.1.0",
            "description": f"{p} plugin",
            "author": "Tester",
            "entry_point": "plugin.py",
            "category": "analytics",
            "capabilities": ["data_analysis"]
        }))
    mgr = PluginManager(str(plugin_root))
    res = await mgr.load_all_plugins()
    assert set(res.keys()) == {"pA", "pB"}
    mkt = await mgr.get_marketplace_plugins()
    assert "featured_plugins" in mkt and isinstance(mkt["total_available"], int)