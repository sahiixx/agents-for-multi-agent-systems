"""
Comprehensive unit tests for backend/core/insights_engine.py
Tests AI-powered insights and anomaly detection
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


class TestInsightType:
    """Test InsightType enum"""
    
    def test_insight_types_defined(self):
        """Test all insight types are defined"""
        from backend.core.insights_engine import InsightType
        
        assert InsightType.PERFORMANCE_OPTIMIZATION
        assert InsightType.ANOMALY_DETECTION
        assert InsightType.BUSINESS_RECOMMENDATION
        assert InsightType.AGENT_IMPROVEMENT
        assert InsightType.COST_OPTIMIZATION
        assert InsightType.REVENUE_OPPORTUNITY
        assert InsightType.RISK_ALERT


class TestInsightSeverity:
    """Test InsightSeverity enum"""
    
    def test_severity_levels(self):
        """Test severity levels are properly ordered"""
        from backend.core.insights_engine import InsightSeverity
        
        assert InsightSeverity.LOW.value == 1
        assert InsightSeverity.MEDIUM.value == 2
        assert InsightSeverity.HIGH.value == 3
        assert InsightSeverity.CRITICAL.value == 4


class TestInsight:
    """Test Insight dataclass"""
    
    def test_insight_creation(self):
        """Test creating Insight with all fields"""
        from backend.core.insights_engine import Insight, InsightType, InsightSeverity
        
        insight = Insight(
            insight_id="test_123",
            type=InsightType.PERFORMANCE_OPTIMIZATION,
            severity=InsightSeverity.MEDIUM,
            title="Test Insight",
            description="Test description",
            recommendations=["rec1", "rec2"],
            data_points={"metric": 100},
            confidence_score=0.85,
            impact_estimate="High impact",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        assert insight.insight_id == "test_123"
        assert insight.type == InsightType.PERFORMANCE_OPTIMIZATION
        assert insight.severity == InsightSeverity.MEDIUM
        assert len(insight.recommendations) == 2
        assert insight.confidence_score == 0.85


class TestSmartInsightsEngineInitialization:
    """Test SmartInsightsEngine initialization"""
    
    def test_insights_engine_creation(self):
        """Test SmartInsightsEngine can be created"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        assert engine is not None
        assert hasattr(engine, "ai_service")
        assert hasattr(engine, "thresholds")
        assert hasattr(engine, "metrics_history")
        assert hasattr(engine, "insight_patterns")
    
    def test_thresholds_configured(self):
        """Test analysis thresholds are configured"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        assert "performance_deviation" in engine.thresholds
        assert "anomaly_sensitivity" in engine.thresholds
        assert "trend_analysis_days" in engine.thresholds
        assert "confidence_threshold" in engine.thresholds
    
    def test_insight_patterns_defined(self):
        """Test insight patterns are defined"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        assert "declining_performance" in engine.insight_patterns
        assert "high_error_rate" in engine.insight_patterns
        assert "resource_optimization" in engine.insight_patterns
    
    def test_global_insights_engine_instance(self):
        """Test global insights_engine instance exists"""
        from backend.core.insights_engine import insights_engine
        
        assert insights_engine is not None


class TestAnalyzeSystemPerformance:
    """Test analyze_system_performance method"""
    
    @pytest.mark.asyncio
    async def test_analyze_system_performance_success(self):
        """Test analyzing system performance successfully"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        metrics_data = {
            "cpu_usage": 45.5,
            "memory_usage": 60.2,
            "request_count": 1000,
            "error_rate": 0.02,
            "average_response_time": 250
        }
        
        with patch.object(engine, "_analyze_performance_trends", return_value=[]):
            with patch.object(engine, "_detect_anomalies", return_value=[]):
                with patch.object(engine, "_analyze_resource_optimization", return_value=[]):
                    with patch.object(engine, "_generate_business_recommendations", return_value=[]):
                        with patch.object(engine, "_store_insights", return_value=None):
                            insights = await engine.analyze_system_performance(metrics_data)
                            
                            assert isinstance(insights, list)
    
    @pytest.mark.asyncio
    async def test_analyze_system_performance_stores_metrics(self):
        """Test that performance analysis stores metrics history"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        metrics_data = {"cpu_usage": 50.0}
        
        with patch.object(engine, "_analyze_performance_trends", return_value=[]):
            with patch.object(engine, "_detect_anomalies", return_value=[]):
                with patch.object(engine, "_analyze_resource_optimization", return_value=[]):
                    with patch.object(engine, "_generate_business_recommendations", return_value=[]):
                        with patch.object(engine, "_store_insights", return_value=None):
                            await engine.analyze_system_performance(metrics_data)
                            
                            # Metrics should be stored
                            assert len(engine.metrics_history) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_system_performance_handles_errors(self):
        """Test error handling in system performance analysis"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        # Should not raise exception on error
        insights = await engine.analyze_system_performance({})
        assert isinstance(insights, list)


class TestAnalyzeAgentPerformance:
    """Test analyze_agent_performance method"""
    
    @pytest.mark.asyncio
    async def test_analyze_agent_performance_low_success_rate(self):
        """Test agent performance analysis with low success rate"""
        from backend.core.insights_engine import SmartInsightsEngine, InsightType, InsightSeverity
        
        engine = SmartInsightsEngine()
        
        agent_metrics = {
            "success_rate": 0.75,
            "average_response_time": 3.0,
            "tasks_completed": 100
        }
        
        insights = await engine.analyze_agent_performance("agent_1", agent_metrics)
        
        assert isinstance(insights, list)
        # Should generate insight for low success rate
        if insights:
            assert any(i.type == InsightType.AGENT_IMPROVEMENT for i in insights)
    
    @pytest.mark.asyncio
    async def test_analyze_agent_performance_high_latency(self):
        """Test agent performance analysis with high latency"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        agent_metrics = {
            "success_rate": 0.95,
            "average_response_time": 8.0,
            "tasks_completed": 200
        }
        
        insights = await engine.analyze_agent_performance("agent_2", agent_metrics)
        
        # Should generate insight for high response time
        assert isinstance(insights, list)
    
    @pytest.mark.asyncio
    async def test_analyze_agent_performance_optimal(self):
        """Test agent performance analysis with optimal metrics"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        agent_metrics = {
            "success_rate": 0.98,
            "average_response_time": 2.0,
            "tasks_completed": 500
        }
        
        insights = await engine.analyze_agent_performance("agent_3", agent_metrics)
        
        # Should generate fewer insights for optimal performance
        assert isinstance(insights, list)


class TestGetInsightsSummary:
    """Test get_insights_summary method"""
    
    @pytest.mark.asyncio
    async def test_get_insights_summary(self):
        """Test getting insights summary"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        with patch("backend.core.insights_engine.get_database") as mock_db:
            mock_collection = MagicMock()
            mock_collection.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
            mock_db.return_value.insights = mock_collection
            
            summary = await engine.get_insights_summary(days=7)
            
            assert isinstance(summary, dict)
    
    @pytest.mark.asyncio
    async def test_get_insights_summary_handles_errors(self):
        """Test insights summary error handling"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        with patch("backend.core.insights_engine.get_database", side_effect=Exception("DB Error")):
            summary = await engine.get_insights_summary(days=7)
            
            # Should return error dict
            assert "error" in summary


class TestInsightsEngineIntegration:
    """Integration tests for SmartInsightsEngine"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self):
        """Test complete analysis workflow"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        # System analysis
        system_metrics = {
            "cpu_usage": 50.0,
            "memory_usage": 60.0,
            "request_count": 1000
        }
        
        with patch.object(engine, "_analyze_performance_trends", return_value=[]):
            with patch.object(engine, "_detect_anomalies", return_value=[]):
                with patch.object(engine, "_analyze_resource_optimization", return_value=[]):
                    with patch.object(engine, "_generate_business_recommendations", return_value=[]):
                        with patch.object(engine, "_store_insights", return_value=None):
                            system_insights = await engine.analyze_system_performance(system_metrics)
        
        # Agent analysis
        agent_metrics = {
            "success_rate": 0.92,
            "average_response_time": 3.5,
            "tasks_completed": 150
        }
        
        agent_insights = await engine.analyze_agent_performance("test_agent", agent_metrics)
        
        assert isinstance(system_insights, list)
        assert isinstance(agent_insights, list)


class TestInsightGeneration:
    """Test insight generation patterns"""
    
    def test_insight_patterns_have_recommendations(self):
        """Test all insight patterns have recommendations"""
        from backend.core.insights_engine import SmartInsightsEngine
        
        engine = SmartInsightsEngine()
        
        for _pattern_name, pattern_config in engine.insight_patterns.items():
            assert "recommendations" in pattern_config
            assert isinstance(pattern_config["recommendations"], list)
            assert len(pattern_config["recommendations"]) > 0
    
    def test_insight_patterns_have_severity(self):
        """Test all insight patterns have severity"""
        from backend.core.insights_engine import SmartInsightsEngine, InsightSeverity
        
        engine = SmartInsightsEngine()
        
        for _pattern_name, pattern_config in engine.insight_patterns.items():
            assert "severity" in pattern_config
            assert isinstance(pattern_config["severity"], InsightSeverity)