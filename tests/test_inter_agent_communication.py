"""
Unit tests for backend/core/inter_agent_communication.py
Focus on message routing, collaboration, and handler behaviors.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.core.inter_agent_communication import (
    InterAgentCommunication,
    AgentMessage,
    MessageType,
    MessagePriority,
)

class MiniAgent(BaseAgent):
    def __init__(self, agent_id, caps):
        super().__init__(agent_id=agent_id, name=f"Agent {agent_id}", description="mini")
        self._caps = caps

    def get_capabilities(self):
        return self._caps

    async def process_task(self, task):
        return {"ok": True, "echo": task}

# Build a minimal orchestrator with an agent registry
def make_orchestrator():
    a1 = MiniAgent("a1", [AgentCapability.DATA_ANALYSIS])
    a2 = MiniAgent("a2", [AgentCapability.WORKFLOW_AUTOMATION])
    orchestrator = type("Orch", (), {})()
    orchestrator.agents = {"a1": a1, "a2": a2}
    return orchestrator

@pytest.mark.asyncio
async def test_send_message_increments_metrics_and_queue():
    iac = InterAgentCommunication(make_orchestrator())
    msg = AgentMessage({"from_agent_id": "a1", "to_agent_id": "a2", "message_type": MessageType.TASK_REQUEST.value})
    ok = await iac.send_message(msg)
    assert ok is True
    assert iac.metrics["messages_sent"] == 1
    assert iac.message_queue.qsize() == 1

@pytest.mark.asyncio
async def test_delegate_task_returns_message_id_and_queues_message():
    iac = InterAgentCommunication(make_orchestrator())
    with patch.object(iac, "send_message", new=AsyncMock(return_value=True)) as sm:
        mid = await iac.delegate_task("a1", "a2", {"task_type": "x", "task_data": {"k": 1}})
        assert isinstance(mid, str) and mid
        sm.assert_awaited()

@pytest.mark.asyncio
async def test_request_collaboration_populates_active_map_and_sends_requests():
    iac = InterAgentCommunication(make_orchestrator())
    with patch.object(iac, "send_message", new=AsyncMock(return_value=True)) as sm:
        cid = await iac.request_collaboration({
            "initiator_agent_id": "a1",
            "participating_agents": ["a1", "a2"],
            "required_capabilities": ["data_analysis", "workflow_automation"],
            "task_flow": ["step1", "step2"],
            "description": "demo"
        })
        assert isinstance(cid, str) and cid
        assert cid in iac.active_collaborations
        # two requests (for both agents)
        assert sm.await_count >= 2

@pytest.mark.asyncio
async def test_handle_task_request_routes_to_agent_and_sends_response():
    iac = InterAgentCommunication(make_orchestrator())
    # Patch send_message to capture response
    sent = {}
    async def capture(message):
        sent["last"] = message
        return True
    iac.send_message = capture

    msg = AgentMessage({
        "from_agent_id":"a1",
        "to_agent_id":"a2",
        "message_type": MessageType.TASK_REQUEST.value,
        "priority": MessagePriority.MEDIUM.value,
        "payload": {"task_type": "process_task", "task_data": {"x": 1}},
        "requires_response": True
    })
    await iac._handle_task_request(msg, iac.orchestrator.agents["a2"])
    assert "last" in sent
    assert sent["last"].message_type == MessageType.TASK_RESPONSE

@pytest.mark.asyncio
async def test_handle_resource_share_updates_target_memory():
    iac = InterAgentCommunication(make_orchestrator())
    tgt = iac.orchestrator.agents["a2"]
    msg = AgentMessage({
        "from_agent_id":"a1",
        "to_agent_id":"a2",
        "message_type": MessageType.RESOURCE_SHARE.value,
        "payload": {
            "resource_type":"data",
            "resource_data":{"a":1},
            "access_level":"read"
        }
    })
    await iac._handle_resource_share(msg, tgt)
    mem = await tgt.get_memory()
    # Ensure a shared resource key is present
    assert any(k.startswith("shared_resource_") for k in mem.keys())

@pytest.mark.asyncio
async def test_start_and_stop_background_processor_is_safe():
    iac = InterAgentCommunication(make_orchestrator())
    await iac.start()
    assert iac.running is True
    await iac.stop()
    assert iac.running is False

@pytest.mark.asyncio
async def test_get_collaboration_status_shape():
    iac = InterAgentCommunication(make_orchestrator())
    with patch.object(iac, "send_message", new=AsyncMock(return_value=True)):
        cid = await iac.request_collaboration({
            "initiator_agent_id": "a1",
            "participating_agents": ["a1"],
            "required_capabilities": ["data_analysis"],
            "task_flow": ["step1"]
        })
    status = await iac.get_collaboration_status(cid)
    assert status["collaboration_id"] == cid
    assert status["total_steps"] == 1