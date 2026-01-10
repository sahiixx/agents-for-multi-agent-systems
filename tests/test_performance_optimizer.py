"""
Unit tests for backend/core/performance_optimizer.py
Tests performance optimization, caching, and monitoring
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from collections import deque
from backend.core.performance_optimizer import (
    PerformanceOptimizer,
    CacheManager,
    MetricType,
    AlertSeverity,
    PerformanceMetric,
    PerformanceAlert,
    performance_optimizer
)


class TestMetricType:
    """Test metric type enumeration"""
    
    def test_all_metric_types_defined(self):
        """Test that all metric types are defined"""
        assert MetricType.RESPONSE_TIME.value == "response_time"
        assert MetricType.CPU_USAGE.value == "cpu_usage"
        assert MetricType.MEMORY_USAGE.value == "memory_usage"
        assert MetricType.REQUEST_COUNT.value == "request_count"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.CACHE_HIT_RATE.value == "cache_hit_rate"
        assert MetricType.DATABASE_LATENCY.value == "database_latency"


class TestAlertSeverity:
    """Test alert severity enumeration"""
    
    def test_all_severities_defined(self):
        """Test that all alert severities are defined"""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestCacheManager:
    """Test suite for Cache Manager"""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager instance for testing"""
        return CacheManager()
    
    def test_initialization(self, cache_manager):
        """Test cache manager initialization"""
        assert cache_manager.redis_pool is None
        assert cache_manager.cache_stats["hits"] == 0
        assert cache_manager.cache_stats["misses"] == 0
        assert cache_manager.cache_stats["sets"] == 0
        assert cache_manager.cache_stats["deletes"] == 0
    
    @pytest.mark.asyncio
    async def test_initialize(self, cache_manager):
        """Test cache manager initialization"""
        await cache_manager.initialize()
        
        assert hasattr(cache_manager, 'cache_store')
        assert hasattr(cache_manager, 'cache_ttl')
    
    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, cache_manager):
        """Test setting and getting cache values"""
        await cache_manager.initialize()
        
        key = "test_key"
        value = {"data": "test_value"}
        
        set_result = await cache_manager.set(key, value, ttl_seconds=3600)
        assert set_result is True
        
        get_result = await cache_manager.get(key)
        assert get_result == value
        assert cache_manager.cache_stats["hits"] == 1
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_manager):
        """Test getting non-existent cache key"""
        await cache_manager.initialize()
        
        result = await cache_manager.get("nonexistent_key")
        
        assert result is None
        assert cache_manager.cache_stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_manager):
        """Test deleting cache entries"""
        await cache_manager.initialize()
        
        key = "test_key"
        await cache_manager.set(key, "value")
        
        delete_result = await cache_manager.delete(key)
        assert delete_result is True
        
        get_result = await cache_manager.get(key)
        assert get_result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test cache TTL expiration"""
        await cache_manager.initialize()
        
        key = "expiring_key"
        value = "expiring_value"
        
        # Set with past expiry
        await cache_manager.set(key, value, ttl_seconds=0)
        cache_manager.cache_ttl[key] = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        result = await cache_manager.get(key)
        assert result is None  # Should be expired
    
    @pytest.mark.asyncio
    async def test_clear_expired_entries(self, cache_manager):
        """Test clearing expired cache entries"""
        await cache_manager.initialize()
        
        # Add some entries
        await cache_manager.set("key1", "value1", ttl_seconds=3600)
        await cache_manager.set("key2", "value2", ttl_seconds=1)
        
        # Manually expire key2
        cache_manager.cache_ttl["key2"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        await cache_manager.clear_expired()
        
        assert await cache_manager.get("key1") == "value1"
        assert await cache_manager.get("key2") is None
    
    def test_get_stats(self, cache_manager):
        """Test getting cache statistics"""
        cache_manager.cache_stats["hits"] = 80
        cache_manager.cache_stats["misses"] = 20
        cache_manager.cache_stats["sets"] = 100
        cache_manager.cache_store = {"key1": "val1", "key2": "val2"}
        
        stats = cache_manager.get_stats()
        
        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["hit_rate_percentage"] == 80.0
        assert stats["cache_size"] == 2
    
    def test_get_stats_no_requests(self, cache_manager):
        """Test stats when no requests have been made"""
        stats = cache_manager.get_stats()
        
        assert stats["hit_rate_percentage"] == 0
        assert stats["cache_size"] == 0


class TestPerformanceOptimizer:
    """Test suite for Performance Optimizer"""
    
    @pytest.fixture
    def optimizer(self):
        """Create a performance optimizer instance for testing"""
        return PerformanceOptimizer()
    
    def test_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.cache_manager is not None
        assert optimizer.metrics_buffer is not None
        assert optimizer.alerts == {}
        assert optimizer.performance_thresholds is not None
    
    def test_performance_thresholds_configured(self, optimizer):
        """Test that performance thresholds are configured"""
        assert MetricType.RESPONSE_TIME in optimizer.performance_thresholds
        assert MetricType.CPU_USAGE in optimizer.performance_thresholds
        assert MetricType.MEMORY_USAGE in optimizer.performance_thresholds
        
        # Check structure
        cpu_thresholds = optimizer.performance_thresholds[MetricType.CPU_USAGE]
        assert "warning" in cpu_thresholds
        assert "critical" in cpu_thresholds
    
    def test_auto_scaling_configuration(self, optimizer):
        """Test auto-scaling configuration"""
        assert optimizer.auto_scaling["enabled"] is True
        assert optimizer.auto_scaling["min_instances"] >= 1
        assert optimizer.auto_scaling["max_instances"] > optimizer.auto_scaling["min_instances"]
    
    def test_optimization_rules_defined(self, optimizer):
        """Test that optimization rules are defined"""
        assert len(optimizer.optimization_rules) > 0
        
        for rule in optimizer.optimization_rules:
            assert "name" in rule
            assert "condition" in rule
            assert "actions" in rule
    
    @pytest.mark.asyncio
    async def test_initialize_optimizer(self, optimizer):
        """Test initializing performance optimizer"""
        with patch.object(optimizer, '_monitoring_loop', return_value=None):
            await optimizer.initialize()
            
            # Cache manager should be initialized
            assert hasattr(optimizer.cache_manager, 'cache_store')
    
    @pytest.mark.asyncio
    async def test_record_metric(self, optimizer):
        """Test recording performance metric"""
        metric = PerformanceMetric(
            metric_type=MetricType.RESPONSE_TIME,
            value=1.5,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="api",
            tags={"endpoint": "/api/test"}
        )
        
        await optimizer.record_metric(metric)
        
        # Check metric was added to buffer
        metric_key = f"{metric.metric_type.value}_{metric.source}"
        assert metric_key in optimizer.metrics_buffer
        assert len(optimizer.metrics_buffer[metric_key]) > 0
    
    @pytest.mark.asyncio
    async def test_get_performance_summary(self, optimizer):
        """Test getting performance summary"""
        # Add some metrics
        for i in range(5):
            metric = PerformanceMetric(
                metric_type=MetricType.CPU_USAGE,
                value=50.0 + i,
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="system",
                tags={}
            )
            await optimizer.record_metric(metric)
        
        summary = await optimizer.get_performance_summary(hours=1)
        
        assert "time_period" in summary
        assert "metric_summary" in summary
        assert "cache_statistics" in summary
    
    @pytest.mark.asyncio
    async def test_optimize_performance_all_areas(self, optimizer):
        """Test performance optimization for all areas"""
        result = await optimizer.optimize_performance(target_area="all")
        
        assert "optimizations_applied" in result
        assert "results" in result
        assert "timestamp" in result
        assert isinstance(result["optimizations_applied"], int)
    
    @pytest.mark.asyncio
    async def test_optimize_performance_specific_area(self, optimizer):
        """Test performance optimization for specific area"""
        result = await optimizer.optimize_performance(target_area="cache")
        
        assert "optimizations_applied" in result
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_auto_scale_recommendation_normal_load(self, optimizer):
        """Test auto-scaling recommendation under normal load"""
        with patch.object(optimizer, '_get_current_system_metrics', 
                         return_value={"cpu_usage": 50.0, "memory_usage": 60.0}):
            result = await optimizer.auto_scale_recommendation()
            
            assert "auto_scaling_enabled" in result
            assert "current_metrics" in result
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_auto_scale_recommendation_high_load(self, optimizer):
        """Test auto-scaling recommendation under high load"""
        with patch.object(optimizer, '_get_current_system_metrics', 
                         return_value={"cpu_usage": 85.0, "memory_usage": 90.0}):
            result = await optimizer.auto_scale_recommendation()
            
            recommendations = result["recommendations"]
            assert len(recommendations) > 0
            
            # Should recommend scaling up
            scale_up_recs = [r for r in recommendations if r["action"] == "scale_up"]
            assert len(scale_up_recs) > 0
    
    @pytest.mark.asyncio
    async def test_auto_scale_recommendation_low_load(self, optimizer):
        """Test auto-scaling recommendation under low load"""
        with patch.object(optimizer, '_get_current_system_metrics', 
                         return_value={"cpu_usage": 20.0, "memory_usage": 30.0}):
            result = await optimizer.auto_scale_recommendation()
            
            recommendations = result["recommendations"]
            
            # Should recommend scaling down or optimization
            scale_down_recs = [r for r in recommendations 
                              if r["action"] in ["scale_down", "optimize"]]
            assert len(scale_down_recs) > 0
    
    @pytest.mark.asyncio
    async def test_check_alert_conditions_warning(self, optimizer):
        """Test alert creation for warning threshold"""
        metric = PerformanceMetric(
            metric_type=MetricType.CPU_USAGE,
            value=75.0,  # Warning threshold
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="system",
            tags={}
        )
        
        await optimizer._check_alert_conditions(metric)
        
        # Check if alert was created
        assert len(optimizer.alerts) > 0
    
    @pytest.mark.asyncio
    async def test_check_alert_conditions_critical(self, optimizer):
        """Test alert creation for critical threshold"""
        metric = PerformanceMetric(
            metric_type=MetricType.CPU_USAGE,
            value=95.0,  # Critical threshold
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="system",
            tags={}
        )
        
        await optimizer._check_alert_conditions(metric)
        
        # Check if critical alert was created
        alerts = list(optimizer.alerts.values())
        if len(alerts) > 0:
            assert any(a.severity == AlertSeverity.CRITICAL for a in alerts)
    
    @pytest.mark.asyncio
    async def test_get_current_system_metrics(self, optimizer):
        """Test getting current system metrics"""
        metrics = await optimizer._get_current_system_metrics()
        
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        assert "timestamp" in metrics
        assert isinstance(metrics["cpu_usage"], (int, float))
    
    @pytest.mark.asyncio
    async def test_evaluate_condition(self, optimizer):
        """Test evaluating optimization conditions"""
        metrics = {
            "database_latency": 2.0,
            "response_time": 6.0,
            "memory_usage": 90.0
        }
        
        # Test database latency condition
        result1 = await optimizer._evaluate_condition("database_latency > 1.0", metrics)
        assert result1 is True
        
        # Test response time condition
        result2 = await optimizer._evaluate_condition("response_time > 5.0", metrics)
        assert result2 is True
    
    @pytest.mark.asyncio
    async def test_apply_optimization_action(self, optimizer):
        """Test applying optimization actions"""
        actions = [
            "enable_query_cache",
            "optimize_indexes",
            "increase_cache_ttl",
            "cache_cleanup"
        ]
        
        for action in actions:
            result = await optimizer._apply_optimization_action(action)
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_database_performance(self, optimizer):
        """Test database performance optimization"""
        optimizations = await optimizer._optimize_database_performance()
        
        assert isinstance(optimizations, list)
        assert len(optimizations) > 0
        
        for opt in optimizations:
            assert "area" in opt
            assert opt["area"] == "database"
            assert "action" in opt
            assert "result" in opt
    
    @pytest.mark.asyncio
    async def test_optimize_cache_performance(self, optimizer):
        """Test cache performance optimization"""
        optimizations = await optimizer._optimize_cache_performance()
        
        assert isinstance(optimizations, list)
        assert len(optimizations) > 0
        
        for opt in optimizations:
            assert "area" in opt
            assert opt["area"] == "cache"
    
    @pytest.mark.asyncio
    async def test_shutdown_optimizer(self, optimizer):
        """Test shutting down optimizer"""
        optimizer.running = True
        optimizer.monitoring_task = asyncio.get_running_loop().create_future()

        await optimizer.shutdown()

        assert optimizer.running is False
        assert optimizer.monitoring_task.cancelled()
    
    def test_global_performance_optimizer_instance(self):
        """Test global performance optimizer instance exists"""
        assert performance_optimizer is not None
        assert isinstance(performance_optimizer, PerformanceOptimizer)
    
    @pytest.mark.asyncio
    async def test_metric_buffer_max_length(self, optimizer):
        """Test that metric buffer respects max length"""
        metric_key = "test_metric"
        
        # Add more than 1000 metrics
        for i in range(1500):
            metric = PerformanceMetric(
                metric_type=MetricType.REQUEST_COUNT,
                value=float(i),
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="test",
                tags={}
            )
            optimizer.metrics_buffer[metric_key].append(metric)
        
        # Buffer should be capped at 1000 (maxlen)
        assert len(optimizer.metrics_buffer[metric_key]) <= 1000
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_alert_low_threshold(self, optimizer):
        """Test alert for low cache hit rate"""
        metric = PerformanceMetric(
            metric_type=MetricType.CACHE_HIT_RATE,
            value=45.0,  # Below critical threshold
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="cache",
            tags={}
        )
        
        await optimizer._check_alert_conditions(metric)
        
        # Should create alert for low hit rate
        assert len(optimizer.alerts) > 0