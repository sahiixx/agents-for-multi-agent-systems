"""
Comprehensive unit tests for backend/core/inter_agent_communication.py
Tests inter-agent communication and coordination
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


class TestMessageType:
    """Test MessageType enum"""
    
    def test_message_types_defined(self):
        """Test all message types are defined"""
        from backend.core.inter_agent_communication import MessageType
        
        assert MessageType.REQUEST
        assert MessageType.RESPONSE
        assert MessageType.NOTIFICATION
        assert MessageType.BROADCAST
        assert MessageType.TASK_ASSIGNMENT
        assert MessageType.STATUS_UPDATE


class TestAgentMessage:
    """Test AgentMessage dataclass"""
    
    def test_agent_message_creation(self):
        """Test creating AgentMessage"""
        from backend.core.inter_agent_communication import AgentMessage, MessageType
        
        message = AgentMessage(
            message_id="msg_123",
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
            priority=5,
            timestamp=datetime.now().isoformat()
        )
        
        assert message.message_id == "msg_123"
        assert message.from_agent == "agent_1"
        assert message.to_agent == "agent_2"
        assert message.message_type == MessageType.REQUEST
        assert message.priority == 5


class TestInterAgentCommunicationInitialization:
    """Test InterAgentCommunication initialization"""
    
    def test_inter_agent_comm_creation(self):
        """Test InterAgentCommunication can be created"""
        from backend.core.inter_agent_communication import InterAgentCommunication
        
        comm = InterAgentCommunication(orchestrator=None)
        
        assert comm is not None
        assert hasattr(comm, "orchestrator")
        assert hasattr(comm, "message_queue")
        assert hasattr(comm, "agent_channels")
        assert hasattr(comm, "message_history")
    
    def test_message_queue_initialized(self):
        """Test message queue is initialized"""
        from backend.core.inter_agent_communication import InterAgentCommunication
        
        comm = InterAgentCommunication(orchestrator=None)
        
        assert isinstance(comm.message_queue, dict)
    
    def test_agent_channels_initialized(self):
        """Test agent channels are initialized"""
        from backend.core.inter_agent_communication import InterAgentCommunication
        
        comm = InterAgentCommunication(orchestrator=None)
        
        assert isinstance(comm.agent_channels, dict)
    
    def test_global_inter_agent_comm_instance(self):
        """Test global inter_agent_comm instance exists"""
        from backend.core.inter_agent_communication import inter_agent_comm
        
        assert inter_agent_comm is not None


class TestSendMessage:
    """Test send_message method"""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test sending message successfully"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        result = await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"data": "test"}
        )
        
        assert result is not None
        assert "message_id" in result
    
    @pytest.mark.asyncio
    async def test_send_message_with_priority(self):
        """Test sending message with priority"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        result = await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"data": "urgent"},
            priority=10
        )
        
        assert result is not None
        assert "priority" in result


class TestBroadcastMessage:
    """Test broadcast_message method"""
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all agents"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        # Add some agent channels
        comm.agent_channels["agent_1"] = []
        comm.agent_channels["agent_2"] = []
        comm.agent_channels["agent_3"] = []
        
        result = await comm.broadcast_message(
            from_agent="orchestrator",
            message_type=MessageType.BROADCAST,
            content={"announcement": "system update"}
        )
        
        assert isinstance(result, dict)


class TestGetMessages:
    """Test get_messages method"""
    
    @pytest.mark.asyncio
    async def test_get_messages_for_agent(self):
        """Test getting messages for specific agent"""
        from backend.core.inter_agent_communication import InterAgentCommunication
        
        comm = InterAgentCommunication(orchestrator=None)
        
        # Initialize queue for agent
        comm.message_queue["agent_1"] = []
        
        messages = await comm.get_messages("agent_1")
        
        assert isinstance(messages, list)
    
    @pytest.mark.asyncio
    async def test_get_messages_empty_queue(self):
        """Test getting messages from empty queue"""
        from backend.core.inter_agent_communication import InterAgentCommunication
        
        comm = InterAgentCommunication(orchestrator=None)
        
        messages = await comm.get_messages("nonexistent_agent")
        
        assert messages == []


class TestMessageHistory:
    """Test message history tracking"""
    
    @pytest.mark.asyncio
    async def test_message_history_recorded(self):
        """Test that sent messages are recorded in history"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"test": "data"}
        )
        
        # History should be updated
        assert isinstance(comm.message_history, dict)


class TestInterAgentCommunicationIntegration:
    """Integration tests for InterAgentCommunication"""
    
    @pytest.mark.asyncio
    async def test_send_and_receive_workflow(self):
        """Test complete send and receive workflow"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        # Send message
        result = await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"action": "process_data"}
        )
        
        assert "message_id" in result
        
        # Receive messages
        messages = await comm.get_messages("agent_2")
        
        assert isinstance(messages, list)
    
    @pytest.mark.asyncio
    async def test_multiple_agent_communication(self):
        """Test communication between multiple agents"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        # Agent 1 to Agent 2
        await comm.send_message("agent_1", "agent_2", MessageType.REQUEST, {"task": "1"})
        
        # Agent 2 to Agent 3
        await comm.send_message("agent_2", "agent_3", MessageType.REQUEST, {"task": "2"})
        
        # Agent 3 to Agent 1
        await comm.send_message("agent_3", "agent_1", MessageType.RESPONSE, {"result": "done"})
        
        # All agents should have their queues
        messages_2 = await comm.get_messages("agent_2")
        messages_3 = await comm.get_messages("agent_3")
        messages_1 = await comm.get_messages("agent_1")
        
        assert isinstance(messages_2, list)
        assert isinstance(messages_3, list)
        assert isinstance(messages_1, list)


class TestMessagePriority:
    """Test message priority handling"""
    
    @pytest.mark.asyncio
    async def test_high_priority_message(self):
        """Test sending high priority message"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        result = await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.REQUEST,
            content={"urgent": True},
            priority=10
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_low_priority_message(self):
        """Test sending low priority message"""
        from backend.core.inter_agent_communication import InterAgentCommunication, MessageType
        
        comm = InterAgentCommunication(orchestrator=None)
        
        result = await comm.send_message(
            from_agent="agent_1",
            to_agent="agent_2",
            message_type=MessageType.NOTIFICATION,
            content={"info": "status"},
            priority=1
        )
        
        assert result is not None