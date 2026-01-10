"""
Inter-Agent Communication System - Enables agents to collaborate on complex tasks
Implements event-driven communication and task delegation between agents
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
import uuid
from enum import Enum

from backend.agents.base_agent import BaseAgent, AgentCapability

logger = logging.getLogger(__name__)

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COLLABORATION_REQUEST = "collaboration_request"
    STATUS_UPDATE = "status_update"
    RESOURCE_SHARE = "resource_share"
    ERROR_NOTIFICATION = "error_notification"
    COMPLETION_NOTICE = "completion_notice"

class MessagePriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AgentMessage:
    """Message between agents"""
    
    def __init__(self, message_data: Dict[str, Any]):
        self.message_id = message_data.get('message_id', str(uuid.uuid4()))
        self.from_agent_id = message_data.get('from_agent_id', '')
        self.to_agent_id = message_data.get('to_agent_id', '')
        self.message_type = MessageType(message_data.get('message_type', 'task_request'))
        self.priority = MessagePriority(message_data.get('priority', 2))
        self.payload = message_data.get('payload', {})
        self.correlation_id = message_data.get('correlation_id', '')  # Links related messages
        self.timestamp = message_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        self.expires_at = message_data.get('expires_at')
        self.requires_response = message_data.get('requires_response', False)

class CollaborationTask:
    """Multi-agent collaborative task"""
    
    def __init__(self, task_data: Dict[str, Any]):
        self.task_id = task_data.get('task_id', str(uuid.uuid4()))
        self.name = task_data.get('name', '')
        self.description = task_data.get('description', '')
        self.initiator_agent_id = task_data.get('initiator_agent_id', '')
        self.participating_agents = set(task_data.get('participating_agents', []))
        self.required_capabilities = task_data.get('required_capabilities', [])
        self.task_flow = task_data.get('task_flow', [])  # Sequence of sub-tasks
        self.shared_context = task_data.get('shared_context', {})
        self.status = task_data.get('status', 'pending')  # pending, active, completed, failed
        self.created_at = task_data.get('created_at', datetime.now(timezone.utc).isoformat())
        self.completed_steps = task_data.get('completed_steps', [])
        self.results = task_data.get('results', {})

class InterAgentCommunication:
    """
    Manages communication and collaboration between AI agents
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.message_queue = asyncio.Queue()
        self.active_collaborations: Dict[str, CollaborationTask] = {}
        self.agent_subscriptions: Dict[str, Set[MessageType]] = {}
        self.message_handlers: Dict[str, callable] = {}
        
        # Communication metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_processed": 0,
            "collaborations_started": 0,
            "collaborations_completed": 0,
            "average_response_time": 0.0
        }
        
        self.running = False
        self.message_processor_task = None
        
        logger.info("Inter-Agent Communication system initialized")
    
    async def start(self):
        """Start the communication system"""
        if self.running:
            return
        
        self.running = True
        self.message_processor_task = asyncio.create_task(self._process_messages())
        logger.info("Inter-Agent Communication system started")
    
    async def stop(self):
        """Stop the communication system"""
        self.running = False
        if self.message_processor_task:
            self.message_processor_task.cancel()
            await asyncio.gather(self.message_processor_task, return_exceptions=True)
        logger.info("Inter-Agent Communication system stopped")
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message between agents"""
        try:
            await self.message_queue.put(message)
            self.metrics["messages_sent"] += 1
            
            logger.info(f"Message queued: {message.message_id} from {message.from_agent_id} to {message.to_agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def request_collaboration(self, task_data: Dict[str, Any]) -> str:
        """Initiate a collaborative task between multiple agents"""
        try:
            collaboration = CollaborationTask(task_data)
            
            # Find agents with required capabilities
            available_agents = await self._find_capable_agents(collaboration.required_capabilities)
            
            if len(available_agents) < len(collaboration.participating_agents):
                logger.warning(f"Insufficient agents for collaboration: {collaboration.task_id}")
                return None
            
            # Update participating agents with capable ones
            collaboration.participating_agents = set(available_agents[:len(collaboration.participating_agents)])
            
            # Store collaboration
            self.active_collaborations[collaboration.task_id] = collaboration
            
            # Send collaboration requests to all participating agents
            for agent_id in collaboration.participating_agents:
                message = AgentMessage({
                    'from_agent_id': collaboration.initiator_agent_id,
                    'to_agent_id': agent_id,
                    'message_type': MessageType.COLLABORATION_REQUEST.value,
                    'priority': MessagePriority.HIGH.value,
                    'correlation_id': collaboration.task_id,
                    'payload': {
                        'collaboration_id': collaboration.task_id,
                        'task_description': collaboration.description,
                        'required_capabilities': collaboration.required_capabilities,
                        'task_flow': collaboration.task_flow,
                        'shared_context': collaboration.shared_context
                    },
                    'requires_response': True
                })
                
                await self.send_message(message)
            
            self.metrics["collaborations_started"] += 1
            logger.info(f"Collaboration initiated: {collaboration.task_id}")
            return collaboration.task_id
            
        except Exception as e:
            logger.error(f"Error initiating collaboration: {e}")
            return None
    
    async def delegate_task(self, from_agent_id: str, to_agent_id: str, task_data: Dict[str, Any]) -> str:
        """Delegate a task from one agent to another"""
        try:
            message_id = str(uuid.uuid4())
            
            message = AgentMessage({
                'message_id': message_id,
                'from_agent_id': from_agent_id,
                'to_agent_id': to_agent_id,
                'message_type': MessageType.TASK_REQUEST.value,
                'priority': task_data.get('priority', MessagePriority.MEDIUM.value),
                'payload': {
                    'task_type': task_data.get('task_type'),
                    'task_data': task_data.get('task_data', {}),
                    'deadline': task_data.get('deadline'),
                    'context': task_data.get('context', {})
                },
                'requires_response': True
            })
            
            await self.send_message(message)
            logger.info(f"Task delegated from {from_agent_id} to {to_agent_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error delegating task: {e}")
            return None
    
    async def share_resource(self, from_agent_id: str, to_agent_ids: List[str], resource_data: Dict[str, Any]) -> bool:
        """Share resources or data between agents"""
        try:
            for to_agent_id in to_agent_ids:
                message = AgentMessage({
                    'from_agent_id': from_agent_id,
                    'to_agent_id': to_agent_id,
                    'message_type': MessageType.RESOURCE_SHARE.value,
                    'priority': MessagePriority.MEDIUM.value,
                    'payload': {
                        'resource_type': resource_data.get('resource_type'),
                        'resource_data': resource_data.get('data', {}),
                        'access_level': resource_data.get('access_level', 'read'),
                        'expiry': resource_data.get('expiry')
                    }
                })
                
                await self.send_message(message)
            
            logger.info(f"Resource shared from {from_agent_id} to {len(to_agent_ids)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Error sharing resource: {e}")
            return False
    
    async def update_collaboration_status(self, collaboration_id: str, agent_id: str, update_data: Dict[str, Any]):
        """Update collaboration status from participating agent"""
        try:
            collaboration = self.active_collaborations.get(collaboration_id)
            if not collaboration:
                return
            
            # Update step completion
            if 'completed_step' in update_data:
                step = update_data['completed_step']
                if step not in collaboration.completed_steps:
                    collaboration.completed_steps.append(step)
            
            # Update results
            if 'results' in update_data:
                collaboration.results[agent_id] = update_data['results']
            
            # Update shared context
            if 'context_update' in update_data:
                collaboration.shared_context.update(update_data['context_update'])
            
            # Check if collaboration is complete
            if len(collaboration.completed_steps) >= len(collaboration.task_flow):
                collaboration.status = 'completed'
                await self._complete_collaboration(collaboration_id)
            
            # Notify other agents of update
            for other_agent_id in collaboration.participating_agents:
                if other_agent_id != agent_id:
                    message = AgentMessage({
                        'from_agent_id': agent_id,
                        'to_agent_id': other_agent_id,
                        'message_type': MessageType.STATUS_UPDATE.value,
                        'priority': MessagePriority.MEDIUM.value,
                        'correlation_id': collaboration_id,
                        'payload': {
                            'collaboration_id': collaboration_id,
                            'update_type': 'progress',
                            'completed_steps': collaboration.completed_steps,
                            'shared_context': collaboration.shared_context
                        }
                    })
                    
                    await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error updating collaboration status: {e}")
    
    async def get_collaboration_status(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a collaboration"""
        collaboration = self.active_collaborations.get(collaboration_id)
        if not collaboration:
            return None
        
        return {
            "collaboration_id": collaboration_id,
            "status": collaboration.status,
            "participating_agents": list(collaboration.participating_agents),
            "completed_steps": collaboration.completed_steps,
            "total_steps": len(collaboration.task_flow),
            "progress_percentage": len(collaboration.completed_steps) / len(collaboration.task_flow) * 100,
            "results": collaboration.results,
            "shared_context": collaboration.shared_context
        }
    
    async def _process_messages(self):
        """Process messages from the queue"""
        while self.running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                start_time = datetime.now(timezone.utc)
                await self._handle_message(message)
                
                # Update metrics
                processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.metrics["messages_processed"] += 1
                
                # Update average response time
                total_messages = self.metrics["messages_processed"]
                current_avg = self.metrics["average_response_time"]
                self.metrics["average_response_time"] = (current_avg * (total_messages - 1) + processing_time) / total_messages
                
            except asyncio.TimeoutError:
                # No messages in queue, continue loop
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """Handle individual message"""
        try:
            # Get target agent
            target_agent = self.orchestrator.agents.get(message.to_agent_id)
            if not target_agent:
                logger.warning(f"Target agent not found: {message.to_agent_id}")
                return
            
            # Route message based on type
            if message.message_type == MessageType.TASK_REQUEST:
                await self._handle_task_request(message, target_agent)
            elif message.message_type == MessageType.COLLABORATION_REQUEST:
                await self._handle_collaboration_request(message, target_agent)
            elif message.message_type == MessageType.RESOURCE_SHARE:
                await self._handle_resource_share(message, target_agent)
            elif message.message_type == MessageType.STATUS_UPDATE:
                await self._handle_status_update(message, target_agent)
            
        except Exception as e:
            logger.error(f"Error handling message {message.message_id}: {e}")
    
    async def _handle_task_request(self, message: AgentMessage, target_agent: BaseAgent):
        """Handle task delegation request"""
        try:
            task_data = message.payload.get('task_data', {})
            task_type = message.payload.get('task_type', 'process_task')
            
            # Execute task with target agent
            result = await target_agent.execute(task_data)
            
            # Send response back if required
            if message.requires_response:
                response_message = AgentMessage({
                    'from_agent_id': message.to_agent_id,
                    'to_agent_id': message.from_agent_id,
                    'message_type': MessageType.TASK_RESPONSE.value,
                    'correlation_id': message.message_id,
                    'payload': {
                        'original_message_id': message.message_id,
                        'result': result,
                        'status': 'completed' if result.get('success') else 'failed'
                    }
                })
                
                await self.send_message(response_message)
            
        except Exception as e:
            logger.error(f"Error handling task request: {e}")
    
    async def _handle_collaboration_request(self, message: AgentMessage, target_agent: BaseAgent):
        """Handle collaboration participation request"""
        try:
            collaboration_id = message.payload.get('collaboration_id')
            task_description = message.payload.get('task_description', '')
            
            # Agent can accept or decline collaboration
            # For now, auto-accept if agent has required capabilities
            accepts_collaboration = True  # Could be based on agent's current load, capabilities, etc.
            
            response_message = AgentMessage({
                'from_agent_id': message.to_agent_id,
                'to_agent_id': message.from_agent_id,
                'message_type': MessageType.TASK_RESPONSE.value,
                'correlation_id': collaboration_id,
                'payload': {
                    'collaboration_id': collaboration_id,
                    'accepts': accepts_collaboration,
                    'agent_capabilities': [cap.value for cap in target_agent.get_capabilities()],
                    'estimated_completion_time': '1-3 hours'
                }
            })
            
            await self.send_message(response_message)
            
        except Exception as e:
            logger.error(f"Error handling collaboration request: {e}")
    
    async def _handle_resource_share(self, message: AgentMessage, target_agent: BaseAgent):
        """Handle resource sharing"""
        try:
            resource_type = message.payload.get('resource_type')
            resource_data = message.payload.get('resource_data', {})
            
            # Store resource in target agent's memory
            resource_key = f"shared_resource_{message.from_agent_id}_{resource_type}"
            await target_agent.update_memory(resource_key, {
                'data': resource_data,
                'source_agent': message.from_agent_id,
                'received_at': datetime.now(timezone.utc).isoformat(),
                'access_level': message.payload.get('access_level', 'read')
            })
            
            logger.info(f"Resource shared with agent {target_agent.agent_id}")
            
        except Exception as e:
            logger.error(f"Error handling resource share: {e}")
    
    async def _handle_status_update(self, message: AgentMessage, target_agent: BaseAgent):
        """Handle status update message"""
        try:
            collaboration_id = message.correlation_id
            update_data = message.payload
            
            # Update agent's context with collaboration status
            await target_agent.update_memory(f"collaboration_{collaboration_id}", update_data)
            
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
    
    async def _find_capable_agents(self, required_capabilities: List[str]) -> List[str]:
        """Find agents that have the required capabilities"""
        capable_agents = []
        
        for agent_id, agent in self.orchestrator.agents.items():
            agent_capabilities = [cap.value for cap in agent.get_capabilities()]
            
            # Check if agent has any of the required capabilities
            if any(cap in agent_capabilities for cap in required_capabilities):
                capable_agents.append(agent_id)
        
        return capable_agents
    
    async def _complete_collaboration(self, collaboration_id: str):
        """Complete a collaboration and notify all participants"""
        try:
            collaboration = self.active_collaborations.get(collaboration_id)
            if not collaboration:
                return
            
            # Send completion notice to all participants
            for agent_id in collaboration.participating_agents:
                message = AgentMessage({
                    'from_agent_id': 'system',
                    'to_agent_id': agent_id,
                    'message_type': MessageType.COMPLETION_NOTICE.value,
                    'correlation_id': collaboration_id,
                    'payload': {
                        'collaboration_id': collaboration_id,
                        'final_results': collaboration.results,
                        'completion_time': datetime.now(timezone.utc).isoformat()
                    }
                })
                
                await self.send_message(message)
            
            self.metrics["collaborations_completed"] += 1
            logger.info(f"Collaboration completed: {collaboration_id}")
            
        except Exception as e:
            logger.error(f"Error completing collaboration: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get communication system metrics"""
        return {
            **self.metrics,
            "active_collaborations": len(self.active_collaborations),
            "queue_size": self.message_queue.qsize(),
            "system_status": "running" if self.running else "stopped"
        }

# Global inter-agent communication instance
inter_agent_comm = InterAgentCommunication(None)  # Will be initialized with orchestrator
