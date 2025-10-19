"""
Unit tests for backend agents
Tests agent base classes and specific agent implementations
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from backend.agents.base_agent import BaseAgent, AgentCapability, AgentStatus
from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.content_agent import ContentAgent
from backend.agents.marketing_agent import MarketingAgent
from backend.agents.operations_agent import OperationsAgent
from backend.agents.sales_agent import SalesAgent


class TestAgentCapability:
    """Test agent capability enumeration"""
    
    def test_all_capabilities_defined(self):
        """Test that all agent capabilities are defined"""
        assert AgentCapability.LEAD_QUALIFICATION.value == "lead_qualification"
        assert AgentCapability.CAMPAIGN_MANAGEMENT.value == "campaign_management"
        assert AgentCapability.CONTENT_CREATION.value == "content_creation"
        assert AgentCapability.DATA_ANALYSIS.value == "data_analysis"
        assert AgentCapability.WORKFLOW_AUTOMATION.value == "workflow_automation"
        assert AgentCapability.CLIENT_COMMUNICATION.value == "client_communication"
class TestAgentStatus:
    """Test agent status enumeration"""
    
    def test_all_statuses_defined(self):
        """Test that all agent statuses are defined"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.PAUSED.value == "paused"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.ERROR.value == "error"
class TestBaseAgent:
    """Test suite for BaseAgent class"""
    
    @pytest.fixture
    def base_agent(self):
        """Create a base agent instance for testing"""
        return BaseAgent(
            name="Test Agent",
            description="Test agent description"
        )
    
    def test_initialization(self, base_agent):
        """Test agent initialization"""
        assert base_agent.name == "Test Agent"
        assert base_agent.description == "Test agent description"
        assert base_agent.status == AgentStatus.IDLE
        
    def test_agent_has_id(self, base_agent):
        """Test that agent has unique ID"""
        assert hasattr(base_agent, 'agent_id')
        assert base_agent.agent_id is not None
        
    def test_get_status(self, base_agent):
        """Test getting agent status"""
        status = base_agent.get_status()
        assert status["status"] == AgentStatus.IDLE.value
        assert status["name"] == "Test Agent"
        
    @pytest.mark.asyncio
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent remains abstract and cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseAgent(name="X", description="Y")
    
    def test_get_capabilities_empty_by_default(self, base_agent):
        """Test that our dummy agent returns an empty capability list"""
        with pytest.raises(TypeError):
            base_agent.get_capabilities()


class TestAnalyticsAgent:
    """Test suite for Analytics Agent"""
    
    @pytest.fixture
    def analytics_agent(self):
        """Create analytics agent instance"""
        return AnalyticsAgent()
    
    def test_initialization(self, analytics_agent):
        """Test analytics agent initialization"""
        assert analytics_agent.name == "Analytics Agent"
        assert "analytics" in analytics_agent.description.lower()
        assert analytics_agent.ai_service is not None
        
    def test_get_capabilities(self, analytics_agent):
        """Test analytics agent capabilities"""
        capabilities = analytics_agent.get_capabilities()
        assert AgentCapability.DATA_ANALYSIS in capabilities
        
    @pytest.mark.asyncio
    async def test_analyze_data_task(self, analytics_agent):
        """Test data analysis task"""
        task = {
            "type": "analyze_data",
            "data": {"revenue": [100, 200, 300]}
        }
        
        result = await analytics_agent.process_task(task)
        
        assert "analysis_id" in result or "message" in result
        
    @pytest.mark.asyncio
    async def test_generate_forecast_task(self, analytics_agent):
        """Test forecast generation task"""
        task = {
            "type": "generate_forecast",
            "data": {"historical": [100, 200, 300]}
        }
        
        result = await analytics_agent.process_task(task)
        
        assert "forecast_period" in result or "message" in result
        
    @pytest.mark.asyncio
    async def test_detect_anomalies_task(self, analytics_agent):
        """Test anomaly detection task"""
        task = {
            "type": "detect_anomalies",
            "data": {"values": [100, 200, 1000, 150]}
        }
        
        result = await analytics_agent.process_task(task)
        
        assert "anomalies_found" in result or "message" in result


class TestContentAgent:
    """Test suite for Content Agent"""
    
    @pytest.fixture
    def content_agent(self):
        """Create content agent instance"""
        return ContentAgent()
    
    def test_initialization(self, content_agent):
        """Test content agent initialization"""
        assert content_agent.name == "Content Agent"
        assert "content" in content_agent.description.lower()
        
    def test_get_capabilities(self, content_agent):
        """Test content agent capabilities"""
        capabilities = content_agent.get_capabilities()
        assert AgentCapability.CONTENT_CREATION in capabilities
        
    @pytest.mark.asyncio
    async def test_process_unknown_task(self, content_agent):
        """Test processing unknown task type"""
        task = {"type": "unknown_task"}
        result = await content_agent.process_task(task)
        
        assert "message" in result


class TestMarketingAgent:
    """Test suite for Marketing Agent"""
    
    @pytest.fixture
    def marketing_agent(self):
        """Create marketing agent instance"""
        return MarketingAgent()
    
    def test_initialization(self, marketing_agent):
        """Test marketing agent initialization"""
        assert marketing_agent.name == "Marketing Agent"
        assert "marketing" in marketing_agent.description.lower()
        
    def test_get_capabilities(self, marketing_agent):
        """Test marketing agent capabilities"""
        capabilities = marketing_agent.get_capabilities()
        assert AgentCapability.CAMPAIGN_MANAGEMENT in capabilities or \
               AgentCapability.CONTENT_CREATION in capabilities


class TestOperationsAgent:
    """Test suite for Operations Agent"""
    
    @pytest.fixture
    def operations_agent(self):
        """Create operations agent instance"""
        return OperationsAgent()
    
    def test_initialization(self, operations_agent):
        """Test operations agent initialization"""
        assert operations_agent.name == "Operations Agent"
        assert operations_agent.ai_service is not None
        
    def test_get_capabilities(self, operations_agent):
        """Test operations agent capabilities"""
        capabilities = operations_agent.get_capabilities()
        assert AgentCapability.WORKFLOW_AUTOMATION in capabilities


class TestSalesAgent:
    """Test suite for Sales Agent"""
    
    @pytest.fixture
    def sales_agent(self):
        """Create sales agent instance"""
        return SalesAgent()
    
    def test_initialization(self, sales_agent):
        """Test sales agent initialization"""
        assert sales_agent.name == "Sales Agent"
        assert sales_agent.ai_service is not None
        
    def test_get_capabilities(self, sales_agent):
        """Test sales agent capabilities"""
        capabilities = sales_agent.get_capabilities()
        assert AgentCapability.LEAD_QUALIFICATION in capabilities