"""
Health check and readiness probe endpoints for Kubernetes.
"""
from typing import Any

from app.infrastructure.sqlite import SQLiteManager


class HealthChecker:
    """Handles health checks and readiness probes."""
    
    def __init__(self, db_manager: SQLiteManager):
        self.db_manager = db_manager
    
    def liveness_probe(self) -> dict[str, Any]:
        """
        Liveness probe: Is the application running?
        Used by Kubernetes to restart unhealthy containers.
        """
        return {
            "status": "alive",
            "service": "reservation-api"
        }
    
    def readiness_probe(self) -> dict[str, Any]:
        """
        Readiness probe: Is the application ready to serve traffic?
        Used by Kubernetes to route traffic only to ready pods.
        """
        try:
            # Check database connectivity
            with self.db_manager.connection() as conn:
                conn.execute("SELECT 1")
            
            return {
                "status": "ready",
                "service": "reservation-api",
                "database": "connected"
            }
        except Exception as e:
            return {
                "status": "not_ready",
                "service": "reservation-api",
                "database": "disconnected",
                "error": str(e)
            }
    
    def startup_probe(self) -> dict[str, Any]:
        """
        Startup probe: Has the application finished initializing?
        Used by Kubernetes to know when to start liveness/readiness checks.
        """
        try:
            with self.db_manager.connection() as conn:
                conn.execute("SELECT COUNT(*) FROM plateaux")
            
            return {
                "status": "started",
                "service": "reservation-api"
            }
        except Exception as e:
            return {
                "status": "starting",
                "service": "reservation-api",
                "error": str(e)
            }
