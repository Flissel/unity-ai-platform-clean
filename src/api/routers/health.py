"""Health check endpoints for monitoring system status."""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.models import HealthStatus, ServiceHealth, HealthResponse
from ...core.database import get_database_manager
from ...core.cache import get_cache_manager
from ...services.n8n_service import get_n8n_service
from ...services.autogen_service import get_autogen_service
from ...services.code_execution_service import get_code_execution_service
from ...services.workflow_service import get_workflow_service
from ..dependencies import RequireApiKey

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter()


class SystemInfo(BaseModel):
    """System information model."""
    name: str
    version: str
    environment: str
    uptime: float
    timestamp: datetime
    python_version: str
    platform: str


class DetailedHealthResponse(BaseModel):
    """Detailed health response model."""
    status: HealthStatus
    timestamp: datetime
    uptime: float
    services: Dict[str, ServiceHealth]
    system_info: SystemInfo
    metrics: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def basic_health_check():
    """Basic health check endpoint for load balancers."""
    try:
        # Quick health check - just verify core services are responsive
        cache_manager = get_cache_manager()
        db_manager = get_database_manager()
        
        # Basic connectivity checks
        cache_healthy = await cache_manager.health_check()
        db_healthy = await db_manager.health_check()
        
        overall_status = HealthStatus.HEALTHY if (cache_healthy and db_healthy) else HealthStatus.UNHEALTHY
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            message="System is operational" if overall_status == HealthStatus.HEALTHY else "System has issues"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            message=f"Health check failed: {str(e)}"
        )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    _: bool = Depends(RequireApiKey)
):
    """Detailed health check with service status and metrics."""
    import time
    import sys
    import platform
    
    start_time = time.time()
    services = {}
    
    try:
        # Check database
        try:
            db_manager = get_database_manager()
            db_healthy = await db_manager.health_check()
            services["database"] = ServiceHealth(
                name="database",
                status=HealthStatus.HEALTHY if db_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={"type": "postgresql", "connected": db_healthy}
            )
        except Exception as e:
            services["database"] = ServiceHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Check cache (Redis)
        try:
            cache_start = time.time()
            cache_manager = get_cache_manager()
            cache_healthy = await cache_manager.health_check()
            services["cache"] = ServiceHealth(
                name="cache",
                status=HealthStatus.HEALTHY if cache_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - cache_start,
                details={"type": "redis", "connected": cache_healthy}
            )
        except Exception as e:
            services["cache"] = ServiceHealth(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Check n8n service
        try:
            n8n_start = time.time()
            n8n_service = await get_n8n_service()
            n8n_healthy = await n8n_service.health_check()
            services["n8n"] = ServiceHealth(
                name="n8n",
                status=HealthStatus.HEALTHY if n8n_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - n8n_start,
                details={"type": "workflow_engine", "connected": n8n_healthy}
            )
        except Exception as e:
            services["n8n"] = ServiceHealth(
                name="n8n",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Check AutoGen service
        try:
            autogen_start = time.time()
            autogen_service = await get_autogen_service()
            autogen_healthy = await autogen_service.health_check()
            services["autogen"] = ServiceHealth(
                name="autogen",
                status=HealthStatus.HEALTHY if autogen_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - autogen_start,
                details={"type": "ai_agents", "connected": autogen_healthy}
            )
        except Exception as e:
            services["autogen"] = ServiceHealth(
                name="autogen",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Check code execution service
        try:
            code_start = time.time()
            code_service = await get_code_execution_service()
            code_healthy = await code_service.health_check()
            services["code_execution"] = ServiceHealth(
                name="code_execution",
                status=HealthStatus.HEALTHY if code_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - code_start,
                details={"type": "code_sandbox", "connected": code_healthy}
            )
        except Exception as e:
            services["code_execution"] = ServiceHealth(
                name="code_execution",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Check workflow service
        try:
            workflow_start = time.time()
            workflow_service = await get_workflow_service()
            workflow_healthy = await workflow_service.health_check()
            services["workflow"] = ServiceHealth(
                name="workflow",
                status=HealthStatus.HEALTHY if workflow_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - workflow_start,
                details={"type": "orchestrator", "connected": workflow_healthy}
            )
        except Exception as e:
            services["workflow"] = ServiceHealth(
                name="workflow",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Determine overall status
        healthy_services = sum(1 for service in services.values() if service.status == HealthStatus.HEALTHY)
        total_services = len(services)
        
        if healthy_services == total_services:
            overall_status = HealthStatus.HEALTHY
        elif healthy_services > total_services // 2:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        # System information
        system_info = SystemInfo(
            name="Unity AI",
            version="2.0.0",
            environment=settings.api.environment,
            uptime=time.time() - start_time,  # This would be actual uptime in production
            timestamp=datetime.utcnow(),
            python_version=sys.version,
            platform=platform.platform()
        )
        
        # Collect metrics
        metrics = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "response_time": time.time() - start_time,
            "memory_usage": await _get_memory_usage(),
            "cpu_usage": await _get_cpu_usage()
        }
        
        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime=time.time() - start_time,
            services=services,
            system_info=system_info,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/services")
async def services_health(
    _: bool = Depends(RequireApiKey)
) -> Dict[str, ServiceHealth]:
    """Get health status of individual services."""
    services = {}
    
    # Check each service individually
    service_checks = [
        ("database", lambda: get_database_manager().health_check()),
        ("cache", lambda: get_cache_manager().health_check()),
        ("n8n", lambda: get_n8n_service().health_check()),
        ("autogen", lambda: get_autogen_service().health_check()),
        ("code_execution", lambda: get_code_execution_service().health_check()),
        ("workflow", lambda: get_workflow_service().health_check())
    ]
    
    for service_name, health_check in service_checks:
        start_time = time.time()
        try:
            if service_name in ["n8n", "autogen", "code_execution", "workflow"]:
                service = await health_check()
                is_healthy = await service.health_check()
            else:
                is_healthy = await health_check()
            
            services[service_name] = ServiceHealth(
                name=service_name,
                status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={"connected": is_healthy}
            )
        except Exception as e:
            services[service_name] = ServiceHealth(
                name=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    return services


@router.get("/health/metrics")
async def health_metrics(
    _: bool = Depends(RequireApiKey)
) -> Dict[str, Any]:
    """Get system metrics for monitoring."""
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "memory_usage": await _get_memory_usage(),
                "cpu_usage": await _get_cpu_usage(),
                "disk_usage": await _get_disk_usage()
            },
            "services": {
                "database": await _get_database_metrics(),
                "cache": await _get_cache_metrics(),
                "n8n": await _get_n8n_metrics(),
                "autogen": await _get_autogen_metrics(),
                "code_execution": await _get_code_execution_metrics()
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )


# Helper functions for metrics collection
async def _get_memory_usage() -> Dict[str, float]:
    """Get memory usage statistics."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}


async def _get_cpu_usage() -> Dict[str, float]:
    """Get CPU usage statistics."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        return {
            "percent": cpu_percent,
            "count": cpu_count,
            "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}


async def _get_disk_usage() -> Dict[str, float]:
    """Get disk usage statistics."""
    try:
        import psutil
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}


async def _get_database_metrics() -> Dict[str, Any]:
    """Get database-specific metrics."""
    try:
        db_manager = get_database_manager()
        # Add database-specific metrics here
        return {
            "connected": await db_manager.health_check(),
            "pool_size": "N/A",  # Would need to implement in DatabaseManager
            "active_connections": "N/A"
        }
    except Exception as e:
        return {"error": str(e)}


async def _get_cache_metrics() -> Dict[str, Any]:
    """Get cache-specific metrics."""
    try:
        cache_manager = get_cache_manager()
        info = await cache_manager.get_info()
        return info
    except Exception as e:
        return {"error": str(e)}


async def _get_n8n_metrics() -> Dict[str, Any]:
    """Get n8n-specific metrics."""
    try:
        n8n_service = await get_n8n_service()
        stats = await n8n_service.get_workflow_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}


async def _get_autogen_metrics() -> Dict[str, Any]:
    """Get AutoGen-specific metrics."""
    try:
        autogen_service = await get_autogen_service()
        stats = await autogen_service.get_usage_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}


async def _get_code_execution_metrics() -> Dict[str, Any]:
    """Get code execution service metrics."""
    try:
        code_service = await get_code_execution_service()
        stats = await code_service.get_usage_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}