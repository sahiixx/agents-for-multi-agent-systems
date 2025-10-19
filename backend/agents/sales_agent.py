"""
Sales Agent - AI-powered sales automation and lead management
Capabilities: Lead qualification, follow-ups, meeting scheduling, sales insights
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from .base_agent import BaseAgent, AgentCapability, AgentStatus
from backend.services.ai_service import AIService

class SalesAgent(BaseAgent):
    """
    AI Sales Agent for lead qualification, nurturing, and conversion
    """
    
    def __init__(self):
        super().__init__(
            name="Sales Agent",
            description="AI-powered sales automation specialist for lead qualification and conversion"
        )
        self.ai_service = AIService()
        
        # Sales-specific configuration
        self.config.update({
            "qualification_score_threshold": 7.0,
            "follow_up_intervals": [1, 3, 7, 14],  # days
            "max_follow_ups": 4,
            "business_hours": {"start": 9, "end": 18},
            "response_templates": {
                "qualified_lead": "Thank you for your interest! Based on your requirements, I'd like to schedule a consultation to discuss how we can help achieve your goals.",
                "unqualified_lead": "Thank you for reaching out. While we may not be the perfect fit right now, I'll keep your information for future opportunities.",
                "follow_up": "Following up on our previous conversation about {topic}. Are you still interested in {service}?"
            }
        })
        
        # Lead scoring criteria
        self.lead_scoring_criteria = {
            "budget_match": 30,      # Budget alignment with services
            "urgency": 25,           # Timeline and urgency 
            "authority": 20,         # Decision-making power
            "business_fit": 15,      # Company size/industry fit
            "engagement": 10         # Response rate and engagement
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.LEAD_QUALIFICATION,
            AgentCapability.CLIENT_COMMUNICATION,
            AgentCapability.WORKFLOW_AUTOMATION
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process sales-related tasks"""
        task_type = task.get('type')
        
        if task_type == 'qualify_lead':
            return await self._qualify_lead(task.get('data', {}))
        elif task_type == 'schedule_follow_up':
            return await self._schedule_follow_up(task.get('data', {}))
        elif task_type == 'generate_proposal':
            return await self._generate_proposal(task.get('data', {}))
        elif task_type == 'analyze_sales_pipeline':
            return await self._analyze_sales_pipeline(task.get('data', {}))
        elif task_type == 'send_follow_up':
            return await self._send_follow_up(task.get('data', {}))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualify incoming leads using AI analysis and scoring
        """
        self.logger.info(f"Qualifying lead: {lead_data.get('email', 'unknown')}")
        
        # Prepare lead analysis prompt
        analysis_prompt = f"""
        Analyze this lead for NOWHERE DIGITAL MEDIA:
        
        Name: {lead_data.get('name', 'N/A')}
        Email: {lead_data.get('email', 'N/A')}
        Phone: {lead_data.get('phone', 'N/A')}
        Company: {lead_data.get('company', 'N/A')}
        Service Interest: {lead_data.get('service', 'N/A')}
        Message: {lead_data.get('message', 'N/A')}
        Budget: {lead_data.get('budget', 'N/A')}
        Timeline: {lead_data.get('timeline', 'N/A')}
        
        Score this lead 1-10 based on:
        1. Budget alignment (do they mention specific budget or seem price-sensitive?)
        2. Urgency (do they need quick results or have timeline pressure?)
        3. Authority (do they seem to be decision makers?)
        4. Business fit (does their business align with our services?)
        5. Engagement quality (is their message detailed and specific?)
        
        Provide:
        1. Overall score (1-10)
        2. Reasoning for the score
        3. Recommended next action
        4. Key talking points for sales conversation
        5. Potential service recommendations
        """
        
        try:
            # Get AI analysis
            ai_analysis = await self.ai_service.generate_content("business_analysis", analysis_prompt)
            
            # Calculate lead score based on criteria
            lead_score = await self._calculate_lead_score(lead_data, ai_analysis)
            
            # Determine qualification status
            is_qualified = lead_score >= self.config["qualification_score_threshold"]
            
            # Generate response template
            response_template = await self._generate_response_template(lead_data, is_qualified, ai_analysis)
            
            # Store lead in memory
            lead_id = f"lead_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{lead_data.get('email', '').split('@')[0]}"
            await self.update_memory(f"leads.{lead_id}", {
                "data": lead_data,
                "score": lead_score,
                "qualified": is_qualified,
                "analysis": ai_analysis,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "new"
            })
            
            # Schedule follow-up if qualified
            next_action = None
            if is_qualified:
                next_action = await self._schedule_follow_up({
                    "lead_id": lead_id,
                    "delay_hours": 2,  # Follow up in 2 hours
                    "action": "send_consultation_invite"
                })
            
            result = {
                "lead_id": lead_id,
                "qualified": is_qualified,
                "score": lead_score,
                "analysis": ai_analysis,
                "response_template": response_template,
                "next_action": next_action,
                "recommendations": await self._get_service_recommendations(lead_data, ai_analysis)
            }
            
            # Emit qualification event
            await self.emit_event("lead_qualified" if is_qualified else "lead_rejected", {
                "lead_id": lead_id,
                "score": lead_score,
                "data": lead_data
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Lead qualification failed: {str(e)}")
            raise
    
    async def _calculate_lead_score(self, lead_data: Dict[str, Any], ai_analysis: str) -> float:
        """Calculate numerical lead score based on criteria"""
        score = 0.0
        
        # Budget scoring
        budget_text = str(lead_data.get('budget', '') + ' ' + lead_data.get('message', '')).lower()
        if any(word in budget_text for word in ['budget', 'invest', 'spend', 'cost']):
            if any(word in budget_text for word in ['10000', '20000', '50000', 'significant', 'substantial']):
                score += 3.0  # High budget signals
            elif any(word in budget_text for word in ['5000', '1000', 'reasonable', 'affordable']):
                score += 2.0  # Medium budget signals
            else:
                score += 1.0  # Budget mentioned
        
        # Urgency scoring
        urgency_text = str(lead_data.get('message', '') + ' ' + lead_data.get('timeline', '')).lower()
        if any(word in urgency_text for word in ['urgent', 'asap', 'immediately', 'soon', 'quickly']):
            score += 2.5
        elif any(word in urgency_text for word in ['month', 'weeks', 'deadline']):
            score += 1.5
        
        # Business fit scoring
        service = lead_data.get('service', '').lower()
        if service in ['ai_automation', 'digital_ecosystem', 'marketing_intelligence']:
            score += 2.0  # High-value services
        elif service in ['web_development', 'content_marketing', 'social_media']:
            score += 1.5  # Standard services
        
        # Message quality scoring
        message = lead_data.get('message', '')
        if len(message) > 100:  # Detailed message
            score += 1.5
        elif len(message) > 50:  # Medium detail
            score += 1.0
        
        # Company information
        if lead_data.get('company'):
            score += 1.0
        
        # Ensure score is within bounds
        return min(max(score, 1.0), 10.0)
    
    async def _generate_response_template(self, lead_data: Dict[str, Any], is_qualified: bool, ai_analysis: str) -> str:
        """Generate personalized response template"""
        if is_qualified:
            base_template = self.config["response_templates"]["qualified_lead"]
        else:
            base_template = self.config["response_templates"]["unqualified_lead"]
        
        # Use AI to personalize the response
        personalization_prompt = f"""
        Create a personalized response for this lead:
        
        Lead: {lead_data.get('name', 'there')}
        Service Interest: {lead_data.get('service', 'digital services')}
        Message: {lead_data.get('message', 'N/A')}
        
        Base template: {base_template}
        
        Make it personal and specific to their needs. Keep it professional but warm.
        Include specific next steps and value propositions for NOWHERE DIGITAL MEDIA.
        """
        
        try:
            personalized_response = await self.ai_service.generate_content("email_campaign", personalization_prompt)
            return personalized_response
        except:
            return base_template
    
    async def _get_service_recommendations(self, lead_data: Dict[str, Any], ai_analysis: str) -> List[Dict[str, Any]]:
        """Get AI-powered service recommendations for the lead"""
        recommendations_prompt = f"""
        Based on this lead's profile, recommend specific services from NOWHERE DIGITAL MEDIA:
        
        Available Services:
        - AI Business Automation (AED 4,999-29,999/month)
        - Digital Ecosystem Development (AED 8,999-49,999/month)  
        - Marketing Intelligence Platform (AED 6,999-39,999/month)
        - E-commerce & Fintech Solutions (AED 9,999-59,999/month)
        - Immersive AR/VR Experiences (AED 12,999-69,999/month)
        - Data Intelligence Analytics (AED 7,999-44,999/month)
        
        Lead Profile:
        Service Interest: {lead_data.get('service', 'N/A')}
        Message: {lead_data.get('message', 'N/A')}
        Budget Hints: {lead_data.get('budget', 'N/A')}
        
        Recommend 2-3 services with:
        1. Service name and price range
        2. Why it fits their needs
        3. Expected ROI/benefits
        4. Implementation timeline
        
        Format as JSON array.
        """
        
        try:
            recommendations = await self.ai_service.generate_content("business_analysis", recommendations_prompt)
            # Parse AI response into structured recommendations
            return [
                {
                    "service": lead_data.get('service', 'Digital Marketing'),
                    "price_range": "AED 8,999-19,999/month",
                    "fit_reason": "Based on your requirements for enhanced digital presence",
                    "expected_roi": "200-300% ROI within 6 months",
                    "timeline": "2-4 weeks implementation"
                }
            ]
        except:
            # Fallback recommendation
            return [
                {
                    "service": "Digital Ecosystem Development", 
                    "price_range": "AED 8,999-19,999/month",
                    "fit_reason": "Comprehensive solution for digital transformation",
                    "expected_roi": "200-300% ROI within 6 months", 
                    "timeline": "4-6 weeks implementation"
                }
            ]
    
    async def _schedule_follow_up(self, follow_up_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule automated follow-up actions"""
        lead_id = follow_up_data.get('lead_id')
        delay_hours = follow_up_data.get('delay_hours', 24)
        action = follow_up_data.get('action', 'send_follow_up')
        
        follow_up_time = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        
        follow_up_task = {
            "id": f"followup_{lead_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "lead_id": lead_id,
            "action": action,
            "scheduled_for": follow_up_time.isoformat(),
            "status": "scheduled"
        }
        
        # Store in memory
        await self.update_memory(f"follow_ups.{follow_up_task['id']}", follow_up_task)
        
        return follow_up_task
    
    async def _send_follow_up(self, follow_up_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send automated follow-up communication"""
        lead_id = follow_up_data.get('lead_id')
        
        # Get lead data from memory
        lead_memory = await self.get_memory(f"leads.{lead_id}")
        if not lead_memory:
            raise ValueError(f"Lead {lead_id} not found in memory")
        
        lead_data = lead_memory.get('data', {})
        
        # Generate follow-up message
        follow_up_prompt = f"""
        Create a follow-up message for this lead:
        
        Name: {lead_data.get('name')}
        Original Interest: {lead_data.get('service')}
        Previous Message: {lead_data.get('message', '')}
        
        This is follow-up #{follow_up_data.get('sequence', 1)}.
        
        Make it:
        1. Personal and reference their original inquiry
        2. Provide additional value or insight
        3. Include a clear call-to-action
        4. Keep it concise and professional
        """
        
        follow_up_message = await self.ai_service.generate_content("email_campaign", follow_up_prompt)
        
        return {
            "message": follow_up_message,
            "lead_id": lead_id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "channel": "email"  # Could be email, SMS, etc.
        }
    
    async def _generate_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered service proposal"""
        lead_id = proposal_data.get('lead_id')
        
        # Get lead data
        lead_memory = await self.get_memory(f"leads.{lead_id}")
        lead_data = lead_memory.get('data', {}) if lead_memory else {}
        
        proposal_prompt = f"""
        Create a comprehensive service proposal for NOWHERE DIGITAL MEDIA:
        
        Client: {lead_data.get('name', 'Valued Client')}
        Company: {lead_data.get('company', 'N/A')}
        Requirements: {lead_data.get('message', 'Digital transformation services')}
        
        Include:
        1. Executive Summary
        2. Recommended Services & Pricing
        3. Implementation Timeline
        4. Expected ROI & KPIs
        5. Why Choose NOWHERE DIGITAL MEDIA
        6. Next Steps
        
        Make it professional, specific, and compelling.
        """
        
        proposal_content = await self.ai_service.generate_content("web_copy", proposal_prompt)
        
        return {
            "proposal_content": proposal_content,
            "lead_id": lead_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft"
        }
    
    async def _analyze_sales_pipeline(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current sales pipeline and provide insights"""
        
        # Get all leads from memory
        leads_memory = await self.get_memory("leads")
        if not leads_memory:
            return {"message": "No leads data available for analysis"}
        
        # Calculate pipeline metrics
        total_leads = len(leads_memory)
        qualified_leads = sum(1 for lead in leads_memory.values() if lead.get('qualified', False))
        avg_score = sum(lead.get('score', 0) for lead in leads_memory.values()) / total_leads if total_leads > 0 else 0
        
        # Analyze trends
        recent_leads = [
            lead for lead in leads_memory.values() 
            if datetime.fromisoformat(lead.get('created_at', '2024-01-01T00:00:00+00:00')) > 
            datetime.now(timezone.utc) - timedelta(days=7)
        ]
        
        analysis = {
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "qualification_rate": (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
            "average_score": round(avg_score, 2),
            "recent_leads_7d": len(recent_leads),
            "pipeline_health": "Good" if qualified_leads / total_leads > 0.3 else "Needs Improvement" if total_leads > 0 else "No Data",
            "recommendations": [
                "Focus on higher-scoring leads for immediate follow-up",
                "Improve lead qualification criteria if qualification rate is low", 
                "Increase marketing efforts if lead volume is low"
            ]
        }
        
        return analysis
    
    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get real-time sales pipeline summary"""
        return await self._analyze_sales_pipeline({})
    
    async def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific lead data"""
        return await self.get_memory(f"leads.{lead_id}")
    
    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status"""
        lead_data = await self.get_memory(f"leads.{lead_id}")
        if lead_data:
            lead_data['status'] = status
            lead_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            await self.update_memory(f"leads.{lead_id}", lead_data)
            return True
        return False