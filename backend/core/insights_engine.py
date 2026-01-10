"""
Smart Insights Engine - AI-powered recommendations, anomaly detection, and self-improvement
Provides intelligent insights for business optimization and agent performance enhancement
"""
import asyncio
import json
import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import numpy as np
from dataclasses import dataclass
from enum import Enum

from backend.services.ai_service import AIService
from backend.database import get_database

logger = logging.getLogger(__name__)

class InsightType(Enum):
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ANOMALY_DETECTION = "anomaly_detection"
    BUSINESS_RECOMMENDATION = "business_recommendation"
    AGENT_IMPROVEMENT = "agent_improvement"
    COST_OPTIMIZATION = "cost_optimization"
    REVENUE_OPPORTUNITY = "revenue_opportunity"
    RISK_ALERT = "risk_alert"

class InsightSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Insight:
    insight_id: str
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    recommendations: List[str]
    data_points: Dict[str, Any]
    confidence_score: float
    impact_estimate: str
    created_at: str
    expires_at: Optional[str] = None

class SmartInsightsEngine:
    """
    AI-powered insights engine for business optimization and anomaly detection
    """
    
    def __init__(self):
        self.ai_service = AIService()
        
        # Analysis thresholds
        self.thresholds = {
            "performance_deviation": 0.2,  # 20% deviation triggers alert
            "anomaly_sensitivity": 2.0,    # Standard deviations for anomaly detection
            "trend_analysis_days": 7,      # Days of data for trend analysis
            "confidence_threshold": 0.7    # Minimum confidence for insights
        }
        
        # Performance metrics tracking
        self.metrics_history = {}
        self.baseline_metrics = {}
        
        # Insight generation patterns
        self.insight_patterns = {
            "declining_performance": {
                "condition": "performance_trend < -0.1",
                "severity": InsightSeverity.MEDIUM,
                "recommendations": [
                    "Review recent configuration changes",
                    "Analyze agent workload distribution", 
                    "Check system resource utilization",
                    "Consider agent optimization or scaling"
                ]
            },
            "high_error_rate": {
                "condition": "error_rate > 0.05",
                "severity": InsightSeverity.HIGH,
                "recommendations": [
                    "Investigate recent error patterns",
                    "Review integration endpoints",
                    "Check data quality and validation",
                    "Implement enhanced error handling"
                ]
            },
            "resource_optimization": {
                "condition": "resource_utilization < 0.3 OR resource_utilization > 0.8",
                "severity": InsightSeverity.MEDIUM,
                "recommendations": [
                    "Optimize resource allocation",
                    "Consider auto-scaling configuration",
                    "Review cost-performance ratio",
                    "Implement intelligent load balancing"
                ]
            }
        }
        
        logger.info("Smart Insights Engine initialized")
    
    async def analyze_system_performance(self, metrics_data: Dict[str, Any]) -> List[Insight]:
        """Analyze overall system performance and generate insights"""
        try:
            insights = []
            
            # Store current metrics
            timestamp = datetime.now(timezone.utc).isoformat()
            self.metrics_history[timestamp] = metrics_data
            
            # Performance trend analysis
            performance_insights = await self._analyze_performance_trends(metrics_data)
            insights.extend(performance_insights)
            
            # Anomaly detection
            anomaly_insights = await self._detect_anomalies(metrics_data)
            insights.extend(anomaly_insights)
            
            # Resource optimization analysis
            resource_insights = await self._analyze_resource_optimization(metrics_data)
            insights.extend(resource_insights)
            
            # AI-powered business recommendations
            business_insights = await self._generate_business_recommendations(metrics_data)
            insights.extend(business_insights)
            
            # Filter insights by confidence threshold
            filtered_insights = [
                insight for insight in insights 
                if insight.confidence_score >= self.thresholds["confidence_threshold"]
            ]
            
            # Store insights in database
            await self._store_insights(filtered_insights)
            
            logger.info(f"Generated {len(filtered_insights)} insights from system analysis")
            return filtered_insights
            
        except Exception as e:
            logger.error(f"Error analyzing system performance: {e}")
            return []
    
    async def analyze_agent_performance(self, agent_id: str, agent_metrics: Dict[str, Any]) -> List[Insight]:
        """Analyze individual agent performance and suggest improvements"""
        try:
            insights = []
            
            # Agent-specific performance analysis
            success_rate = agent_metrics.get('success_rate', 0)
            response_time = agent_metrics.get('average_response_time', 0)
            task_volume = agent_metrics.get('tasks_completed', 0)
            
            # Performance benchmarking
            if success_rate < 0.9:  # Less than 90% success rate
                insights.append(Insight(
                    insight_id=f"agent_performance_{agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                    type=InsightType.AGENT_IMPROVEMENT,
                    severity=InsightSeverity.MEDIUM if success_rate > 0.8 else InsightSeverity.HIGH,
                    title=f"Agent Performance Below Optimal",
                    description=f"Agent {agent_id} has a success rate of {success_rate:.1%}, below the 90% target.",
                    recommendations=[
                        "Review failed task patterns and error logs",
                        "Update agent configuration and thresholds",
                        "Enhance error handling and retry logic",
                        "Consider additional training data or model updates"
                    ],
                    data_points={
                        "current_success_rate": success_rate,
                        "target_success_rate": 0.9,
                        "improvement_needed": 0.9 - success_rate
                    },
                    confidence_score=0.95,
                    impact_estimate="10-20% performance improvement",
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            
            # Response time analysis
            if response_time > 5.0:  # More than 5 seconds average
                insights.append(Insight(
                    insight_id=f"agent_latency_{agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                    type=InsightType.PERFORMANCE_OPTIMIZATION,
                    severity=InsightSeverity.MEDIUM,
                    title="Agent Response Time Optimization Needed",
                    description=f"Agent {agent_id} average response time is {response_time:.2f}s, above optimal range.",
                    recommendations=[
                        "Optimize AI model inference speed",
                        "Implement response caching for common queries",
                        "Review database query performance",
                        "Consider parallel processing for complex tasks"
                    ],
                    data_points={
                        "current_response_time": response_time,
                        "target_response_time": 3.0,
                        "optimization_potential": response_time - 3.0
                    },
                    confidence_score=0.85,
                    impact_estimate="30-50% latency reduction",
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            
            # AI-powered improvement recommendations
            ai_insights = await self._generate_ai_improvement_suggestions(agent_id, agent_metrics)
            insights.extend(ai_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing agent performance: {e}")
            return []
    
    async def detect_business_anomalies(self, business_data: Dict[str, Any]) -> List[Insight]:
        """Detect anomalies in business metrics and operations"""
        try:
            insights = []
            
            # Revenue anomaly detection
            revenue_data = business_data.get('revenue', {})
            if revenue_data:
                revenue_insights = await self._detect_revenue_anomalies(revenue_data)
                insights.extend(revenue_insights)
            
            # Customer behavior anomalies
            customer_data = business_data.get('customers', {})
            if customer_data:
                customer_insights = await self._detect_customer_anomalies(customer_data)
                insights.extend(customer_insights)
            
            # Operational anomalies
            operational_data = business_data.get('operations', {})
            if operational_data:
                operational_insights = await self._detect_operational_anomalies(operational_data)
                insights.extend(operational_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error detecting business anomalies: {e}")
            return []
    
    async def generate_optimization_recommendations(self, context_data: Dict[str, Any]) -> List[Insight]:
        """Generate AI-powered optimization recommendations"""
        try:
            insights = []
            
            # AI-powered analysis prompt
            optimization_prompt = f"""
            Analyze this business performance data and provide optimization recommendations:
            
            System Metrics: {context_data.get('system_metrics', {})}
            Business Metrics: {context_data.get('business_metrics', {})}
            Agent Performance: {context_data.get('agent_performance', {})}
            Recent Trends: {context_data.get('trends', {})}
            
            Identify:
            1. Top 3 optimization opportunities
            2. Cost reduction possibilities
            3. Revenue growth potential
            4. Efficiency improvements
            5. Risk mitigation strategies
            
            Focus on actionable, measurable improvements with clear ROI.
            """
            
            ai_analysis = await self.ai_service.generate_content("business_analysis", optimization_prompt)
            
            # Parse AI analysis into structured insights
            optimization_insight = Insight(
                insight_id=f"optimization_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                type=InsightType.BUSINESS_RECOMMENDATION,
                severity=InsightSeverity.MEDIUM,
                title="AI-Powered Business Optimization Opportunities",
                description="Comprehensive analysis of optimization opportunities based on current performance data.",
                recommendations=[
                    "Implement AI-suggested process improvements",
                    "Focus on high-ROI optimization areas",
                    "Monitor key performance indicators closely",
                    "Execute changes in phases with measurement"
                ],
                data_points={
                    "analysis_scope": "full_system",
                    "data_points_analyzed": len(context_data),
                    "ai_analysis": ai_analysis
                },
                confidence_score=0.8,
                impact_estimate="15-25% efficiency improvement",
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            insights.append(optimization_insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return []
    
    async def _analyze_performance_trends(self, current_metrics: Dict[str, Any]) -> List[Insight]:
        """Analyze performance trends over time"""
        insights = []
        
        try:
            # Get historical data for trend analysis
            recent_data = self._get_recent_metrics(self.thresholds["trend_analysis_days"])
            
            if len(recent_data) < 3:  # Need at least 3 data points for trend
                return insights
            
            # Analyze key metrics trends
            success_rates = [data.get('success_rate', 0) for data in recent_data.values()]
            response_times = [data.get('average_response_time', 0) for data in recent_data.values()]
            
            # Calculate trends
            success_trend = self._calculate_trend(success_rates)
            latency_trend = self._calculate_trend(response_times)
            
            # Generate insights based on trends
            if success_trend < -0.1:  # Declining success rate
                insights.append(Insight(
                    insight_id=f"performance_decline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                    type=InsightType.PERFORMANCE_OPTIMIZATION,
                    severity=InsightSeverity.HIGH,
                    title="Declining System Performance Detected",
                    description=f"System success rate has declined by {abs(success_trend):.1%} over the past {self.thresholds['trend_analysis_days']} days.",
                    recommendations=[
                        "Investigate recent system changes",
                        "Review error logs and failure patterns",
                        "Check resource utilization and scaling",
                        "Consider rollback to previous stable configuration"
                    ],
                    data_points={
                        "trend_direction": "declining",
                        "trend_magnitude": success_trend,
                        "analysis_period_days": self.thresholds["trend_analysis_days"]
                    },
                    confidence_score=0.9,
                    impact_estimate="Immediate attention required",
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
        
        return insights
    
    async def _detect_anomalies(self, current_metrics: Dict[str, Any]) -> List[Insight]:
        """Detect statistical anomalies in system metrics"""
        insights = []
        
        try:
            # Get historical baseline
            historical_data = self._get_recent_metrics(30)  # 30 days of data
            
            if len(historical_data) < 10:  # Need sufficient data for anomaly detection
                return insights
            
            # Analyze each metric for anomalies
            for metric_name, current_value in current_metrics.items():
                if isinstance(current_value, (int, float)):
                    historical_values = [
                        data.get(metric_name, 0) for data in historical_data.values()
                        if isinstance(data.get(metric_name), (int, float))
                    ]
                    
                    if len(historical_values) >= 10:
                        mean_value = statistics.mean(historical_values)
                        std_dev = statistics.stdev(historical_values)
                        
                        # Check for anomaly (value outside 2 standard deviations)
                        if abs(current_value - mean_value) > (self.thresholds["anomaly_sensitivity"] * std_dev):
                            severity = InsightSeverity.HIGH if abs(current_value - mean_value) > (3 * std_dev) else InsightSeverity.MEDIUM
                            
                            insights.append(Insight(
                                insight_id=f"anomaly_{metric_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                                type=InsightType.ANOMALY_DETECTION,
                                severity=severity,
                                title=f"Anomaly Detected in {metric_name}",
                                description=f"Current {metric_name} value ({current_value}) is significantly different from historical average ({mean_value:.2f}).",
                                recommendations=[
                                    f"Investigate cause of {metric_name} anomaly",
                                    "Review recent system changes or external factors",
                                    "Monitor closely for pattern development",
                                    "Consider temporary adjustments if needed"
                                ],
                                data_points={
                                    "current_value": current_value,
                                    "historical_average": mean_value,
                                    "standard_deviation": std_dev,
                                    "deviation_magnitude": abs(current_value - mean_value) / std_dev
                                },
                                confidence_score=0.85,
                                impact_estimate="Monitor and investigate",
                                created_at=datetime.now(timezone.utc).isoformat()
                            ))
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return insights
    
    async def _analyze_resource_optimization(self, metrics_data: Dict[str, Any]) -> List[Insight]:
        """Analyze resource utilization for optimization opportunities"""
        insights = []
        
        try:
            cpu_usage = metrics_data.get('cpu_utilization', 0)
            memory_usage = metrics_data.get('memory_utilization', 0)
            
            # Under-utilization detection
            if cpu_usage < 0.3 and memory_usage < 0.3:
                insights.append(Insight(
                    insight_id=f"resource_underutilization_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                    type=InsightType.COST_OPTIMIZATION,
                    severity=InsightSeverity.MEDIUM,
                    title="Resource Under-utilization Detected",
                    description=f"System resources are under-utilized (CPU: {cpu_usage:.1%}, Memory: {memory_usage:.1%}). Cost optimization opportunity identified.",
                    recommendations=[
                        "Consider downsizing server resources",
                        "Implement auto-scaling to reduce idle costs",
                        "Consolidate workloads if possible",
                        "Review subscription tiers for cost savings"
                    ],
                    data_points={
                        "cpu_utilization": cpu_usage,
                        "memory_utilization": memory_usage,
                        "cost_savings_potential": "20-40%"
                    },
                    confidence_score=0.8,
                    impact_estimate="20-40% cost reduction",
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            
            # Over-utilization detection
            elif cpu_usage > 0.8 or memory_usage > 0.8:
                insights.append(Insight(
                    insight_id=f"resource_overutilization_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                    type=InsightType.PERFORMANCE_OPTIMIZATION,
                    severity=InsightSeverity.HIGH,
                    title="Resource Over-utilization Detected",
                    description=f"System resources are over-utilized (CPU: {cpu_usage:.1%}, Memory: {memory_usage:.1%}). Performance degradation risk identified.",
                    recommendations=[
                        "Scale up server resources immediately",
                        "Implement load balancing",
                        "Optimize resource-intensive processes",
                        "Consider distributed architecture"
                    ],
                    data_points={
                        "cpu_utilization": cpu_usage,
                        "memory_utilization": memory_usage,
                        "performance_risk": "high"
                    },
                    confidence_score=0.95,
                    impact_estimate="Immediate scaling required",
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing resource optimization: {e}")
        
        return insights
    
    async def _generate_business_recommendations(self, metrics_data: Dict[str, Any]) -> List[Insight]:
        """Generate AI-powered business recommendations"""
        insights = []
        
        try:
            # AI analysis for business optimization
            business_prompt = f"""
            Based on these system performance metrics, generate business optimization recommendations:
            
            Metrics: {json.dumps(metrics_data, indent=2)}
            
            Consider:
            1. Revenue optimization opportunities
            2. Customer experience improvements  
            3. Operational efficiency gains
            4. Cost reduction strategies
            5. Growth acceleration tactics
            
            Provide specific, actionable recommendations with estimated impact.
            """
            
            ai_recommendations = await self.ai_service.generate_content("business_analysis", business_prompt)
            
            # Create structured insight from AI analysis
            business_insight = Insight(
                insight_id=f"business_rec_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                type=InsightType.BUSINESS_RECOMMENDATION,
                severity=InsightSeverity.MEDIUM,
                title="AI-Generated Business Optimization Recommendations",
                description="Comprehensive business recommendations based on current system performance and industry best practices.",
                recommendations=[
                    "Review AI-generated recommendations for implementation",
                    "Prioritize high-impact, low-effort optimizations",
                    "Develop implementation timeline with milestones",
                    "Monitor KPIs to measure improvement impact"
                ],
                data_points={
                    "ai_analysis": ai_recommendations,
                    "metrics_analyzed": list(metrics_data.keys()),
                    "recommendation_source": "ai_powered"
                },
                confidence_score=0.75,
                impact_estimate="10-30% business improvement",
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            insights.append(business_insight)
            
        except Exception as e:
            logger.error(f"Error generating business recommendations: {e}")
        
        return insights
    
    async def _generate_ai_improvement_suggestions(self, agent_id: str, agent_metrics: Dict[str, Any]) -> List[Insight]:
        """Generate AI-powered agent improvement suggestions"""
        insights = []
        
        try:
            improvement_prompt = f"""
            Analyze this AI agent's performance and suggest improvements:
            
            Agent ID: {agent_id}
            Performance Metrics: {json.dumps(agent_metrics, indent=2)}
            
            Suggest improvements for:
            1. Task execution efficiency
            2. Error reduction strategies
            3. Response time optimization
            4. Learning and adaptation
            5. Integration enhancements
            
            Focus on actionable technical improvements.
            """
            
            ai_suggestions = await self.ai_service.generate_content("technical_analysis", improvement_prompt)
            
            improvement_insight = Insight(
                insight_id=f"agent_improvement_{agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                type=InsightType.AGENT_IMPROVEMENT,
                severity=InsightSeverity.MEDIUM,
                title=f"AI Agent Improvement Suggestions - {agent_id}",
                description="AI-generated technical improvements for enhanced agent performance.",
                recommendations=[
                    "Implement suggested technical optimizations",
                    "Update agent configuration parameters",
                    "Enhance error handling mechanisms",
                    "Monitor performance after improvements"
                ],
                data_points={
                    "agent_id": agent_id,
                    "current_metrics": agent_metrics,
                    "ai_suggestions": ai_suggestions
                },
                confidence_score=0.8,
                impact_estimate="15-25% performance gain",
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            insights.append(improvement_insight)
            
        except Exception as e:
            logger.error(f"Error generating AI improvement suggestions: {e}")
        
        return insights
    
    def _get_recent_metrics(self, days: int) -> Dict[str, Any]:
        """Get metrics from the last N days"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        recent_metrics = {}
        for timestamp_str, metrics in self.metrics_history.items():
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if timestamp >= cutoff_time:
                recent_metrics[timestamp_str] = metrics
        
        return recent_metrics
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction and magnitude"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0
        
        # Return normalized trend (-1 to 1)
        return correlation * (values[-1] - values[0]) / (max(values) - min(values) + 0.001)
    
    async def _store_insights(self, insights: List[Insight]):
        """Store insights in database"""
        try:
            db = get_database()
            
            for insight in insights:
                await db.insights.insert_one({
                    "insight_id": insight.insight_id,
                    "type": insight.type.value,
                    "severity": insight.severity.value,
                    "title": insight.title,
                    "description": insight.description,
                    "recommendations": insight.recommendations,
                    "data_points": insight.data_points,
                    "confidence_score": insight.confidence_score,
                    "impact_estimate": insight.impact_estimate,
                    "created_at": insight.created_at,
                    "expires_at": insight.expires_at
                })
            
        except Exception as e:
            logger.error(f"Error storing insights: {e}")
    
    async def get_insights_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent insights"""
        try:
            db = get_database()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get recent insights
            insights_cursor = db.insights.find({
                "created_at": {"$gte": cutoff_date.isoformat()}
            })
            
            insights = await insights_cursor.to_list(length=None)
            
            # Summarize by type and severity
            summary = {
                "total_insights": len(insights),
                "by_type": {},
                "by_severity": {},
                "top_recommendations": [],
                "critical_alerts": []
            }
            
            for insight in insights:
                insight_type = insight.get('type', 'unknown')
                severity = insight.get('severity', 'low')
                
                summary["by_type"][insight_type] = summary["by_type"].get(insight_type, 0) + 1
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
                
                # Collect critical alerts
                if severity == InsightSeverity.CRITICAL.value:
                    summary["critical_alerts"].append({
                        "title": insight.get('title'),
                        "description": insight.get('description'),
                        "created_at": insight.get('created_at')
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting insights summary: {e}")
            return {"error": "Failed to get insights summary"}

# Global insights engine instance
insights_engine = SmartInsightsEngine()
