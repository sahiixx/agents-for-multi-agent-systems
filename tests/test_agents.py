"""
Unit tests for backend agents:
- BaseAgent orchestration and lifecycle
- AnalyticsAgent, ContentAgent, MarketingAgent basic behaviors
- OperationsAgent and SalesAgent core flows (with AIService mocked)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, timedelta

from backend.agents.base_agent import BaseAgent, AgentCapability, AgentStatus
from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.content_agent import ContentAgent
from backend.agents.marketing_agent import MarketingAgent
from backend.agents.operations_agent import OperationsAgent
from backend.agents.sales_agent import SalesAgent


class DummyAgent(BaseAgent):
    """Minimal agent for exercising BaseAgent.execute paths."""
    def __init__(self, should_fail: bool = False):
        super().__init__(name="Dummy Agent", description="Test")
        self._should_fail = should_fail

    def get_capabilities(self):
        return [AgentCapability.WORKFLOW_AUTOMATION]

    async def process_task(self, task):
        if self._should_fail:
            raise RuntimeError("boom")
        # Echo payload
        return {"echo": task.get("payload", {}), "handled": True}


@pytest.mark.asyncio
async def test_base_agent_execute_success_updates_memory_and_metrics():
    agent = DummyAgent()
    task = {"id": "t-1", "type": "noop", "payload": {"a": 1}}
    result = await agent.execute(task)

    # Contract
    assert result["success"] is True
    assert result["task_id"] == "t-1"
    assert result["agent_id"] == agent.agent_id
    assert result["result"]["handled"] is True

    # Memory
    mem = await agent.get_memory("tasks")
    assert "t-1" in mem
    assert "result" in mem["t-1"]

    # Metrics and status
    assert agent.metrics["tasks_completed"] == 1
    assert agent.metrics["success_rate"] == 1.0
    assert agent.status in (AgentStatus.IDLE, AgentStatus.COMPLETED)


@pytest.mark.asyncio
async def test_base_agent_execute_failure_path_sets_error_and_metrics():
    agent = DummyAgent(should_fail=True)
    task = {"id": "t-err", "type": "failing"}
    result = await agent.execute(task)

    assert result["success"] is False
    assert result["task_id"] == "t-err"
    assert "error" in result
    assert agent.metrics["tasks_failed"] == 1
    assert agent.metrics["success_rate"] == 0.0
    assert agent.status in (AgentStatus.IDLE, AgentStatus.ERROR)


def test_base_agent_configuration_and_status_snapshot():
    agent = DummyAgent()
    agent.configure({"k1": "v1", "k2": 2})
    snap = agent.get_status()

    assert snap["name"] == "Dummy Agent"
    assert "workflow_automation" in snap["capabilities"]
    assert isinstance(snap["uptime"], float)
    assert agent.config["k1"] == "v1" and agent.config["k2"] == 2


@pytest.mark.asyncio
async def test_base_agent_pause_resume_reset_flow():
    agent = DummyAgent()
    await agent.pause()
    assert agent.status == AgentStatus.PAUSED
    await agent.resume()
    assert agent.status == AgentStatus.IDLE

    # After executing some tasks, reset clears state
    await agent.execute({"type": "noop"})
    assert agent.metrics["tasks_completed"] == 1
    await agent.reset()
    assert agent.metrics["tasks_completed"] == 0
    assert (await agent.get_memory()) == {}


# Concrete agents with simple branch coverage of process_task handlers

@pytest.mark.asyncio
async def test_analytics_agent_basic_flows():
    agent = AnalyticsAgent()
    res1 = await agent.process_task({"type": "analyze_data", "data": {"x": 1}})
    res2 = await agent.process_task({"type": "generate_forecast"})
    res3 = await agent.process_task({"type": "detect_anomalies"})
    res4 = await agent.process_task({"type": "unknown"})

    assert "insights" in res1
    assert res2.get("message", "").lower().startswith("forecast")
    assert "anomalies_found" in res3
    assert "placeholder" in res4.get("message", "").lower()


@pytest.mark.asyncio
async def test_content_agent_task_routing():
    agent = ContentAgent()
    g = await agent.process_task({"type": "generate_content", "data": {"topic": "SEO"}})
    s = await agent.process_task({"type": "optimize_seo", "data": {"kw": "dubai"}})
    t = await agent.process_task({"type": "translate_content", "data": {"lang": "ar"}})
    u = await agent.process_task({"type": "unknown"})

    assert g["word_count"] >= 100
    assert "seo_score" in s
    assert t["source_language"] == "en"
    assert "placeholder" in u["message"].lower()


@pytest.mark.asyncio
async def test_marketing_agent_task_routing():
    agent = MarketingAgent()
    c = await agent.process_task({"type": "create_campaign"})
    o = await agent.process_task({"type": "optimize_campaign"})
    a = await agent.process_task({"type": "analyze_performance"})
    u = await agent.process_task({"type": "unknown"})

    assert c["status"] == "created"
    assert "optimizations_applied" in o
    assert "metrics" in a
    assert "placeholder" in u["message"].lower()


@pytest.mark.asyncio
async def test_operations_agent_core_flows_with_ai_mock():
    agent = OperationsAgent()
    with patch.object(agent.ai_service, "generate_content", new=AsyncMock(return_value="ok")):
        wf = await agent.process_task({"type": "automate_workflow", "data": {"workflow_type": "client_onboarding"}})
        inv = await agent.process_task({"type": "process_invoice", "data": {"amount": 15000, "client_name": "ACME"}})
        ob = await agent.process_task({"type": "onboard_client", "data": {"client_name": "ACME"}})
        hr = await agent.process_task({"type": "hr_automation", "data": {"task_type": "onboarding"}})
        mon = await agent.process_task({"type": "monitor_workflows"})
        opt = await agent.process_task({"type": "optimize_operations", "data": {"goals": "automation"}})

    # Assertions
    assert "execution_plan" in wf and wf["execution_plan"]["status"] == "initiated"
    assert "payment_probability" in inv and 0.1 <= inv["payment_probability"] <= 1.0
    assert "onboarding_id" in ob and "workflow" in ob
    assert "workflow_steps" in hr
    assert "monitoring_summary" in mon
    assert "optimization_analysis" in opt


@pytest.mark.asyncio
async def test_sales_agent_qualification_flow_with_ai_mock():
    agent = SalesAgent()
    with patch.object(agent.ai_service, "generate_content", new=AsyncMock(return_value="analysis")):
        lead = {
            "name": "John",
            "email": "john@x.com",
            "service": "web_development",
            "message": "We need a site ASAP with ~AED 10,000 budget",
            "budget": "AED 10,000",
            "timeline": "2 weeks",
            "company": "X LLC"
        }
        q = await agent.process_task({"type": "qualify_lead", "data": lead})
        assert "lead_id" in q and "score" in q and "qualified" in q
        # memory should have been updated
        lead_mem = await agent.get_memory("leads")
        assert len(lead_mem) >= 1

        # schedule and send follow-up using stored lead_id
        fu_task = await agent._schedule_follow_up({"lead_id": q["lead_id"], "delay_hours": 1, "action": "send_follow_up"})
        assert fu_task["status"] == "scheduled"

        msg = await agent._send_follow_up({"lead_id": q["lead_id"], "sequence": 2})
        assert "message" in msg


@pytest.mark.asyncio
async def test_sales_agent_update_lead_status_and_pipeline_summary():
    agent = SalesAgent()
    # Seed a lead in memory
    await agent.update_memory("leads.L1", {"data": {"name": "A"}, "score": 7.5, "qualified": True, "created_at": datetime.now(timezone.utc).isoformat()})
    await agent.update_memory("leads.L2", {"data": {"name": "B"}, "score": 4.0, "qualified": False, "created_at": datetime.now(timezone.utc).isoformat()})

    ok = await agent.update_lead_status("L1", "contacted")
    assert ok is True
    lead = await agent.get_lead_by_id("L1")
    assert lead["status"] == "contacted"

    summary = await agent.get_pipeline_summary()
    assert "total_leads" in summary and summary["total_leads"] >= 2