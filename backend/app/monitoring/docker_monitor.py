"""
Docker Container Monitor

Monitors Docker container status, resource usage, and health.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import docker
    from docker.errors import DockerException, NotFound
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
    DockerException = Exception
    NotFound = Exception

logger = logging.getLogger(__name__)


class DockerMonitor:
    """
    Docker container monitoring.

    Provides metrics for:
    - Container status (running/stopped/failed)
    - Container resource usage (CPU, memory)
    - Container logs
    - Container restart count
    - Container uptime
    """

    # Alert thresholds
    MAX_RESTARTS_PER_HOUR = 3
    CONTAINER_CPU_THRESHOLD = 80  # %
    CONTAINER_MEMORY_THRESHOLD = 90  # %

    def __init__(self):
        if not DOCKER_AVAILABLE:
            logger.warning("Docker library not available. Install with: pip install docker")
            self.client = None
            return

        try:
            # Connect to Docker daemon
            self.client = docker.from_env()

            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")

        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None

    def get_container_list(self, all_containers: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of all containers.

        Args:
            all_containers: Include stopped containers if True

        Returns:
            List of container information dictionaries
        """
        if not self.is_available():
            return []

        try:
            containers = self.client.containers.list(all=all_containers)

            container_list = []
            for container in containers:
                container_list.append({
                    "id": container.id[:12],  # Short ID
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "status": container.status,
                    "created": container.attrs.get('Created'),
                    "started": container.attrs.get('State', {}).get('StartedAt'),
                })

            return container_list

        except Exception as e:
            logger.error(f"Error getting container list: {e}")
            return []

    def get_container_stats(self, container_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed statistics for containers.

        Args:
            container_name: Specific container name, or None for all running containers

        Returns:
            Dictionary with container statistics
        """
        if not self.is_available():
            return {"status": "error", "error": "Docker not available"}

        try:
            if container_name:
                containers = [self.client.containers.get(container_name)]
            else:
                containers = self.client.containers.list()

            stats_list = []

            for container in containers:
                try:
                    # Get stats (stream=False for single snapshot)
                    stats = container.stats(stream=False)

                    # Calculate CPU percentage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                   stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = 0.0
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * \
                                      len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [100])) * 100.0

                    # Calculate memory usage
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 1)
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0

                    # Network I/O
                    networks = stats.get('networks', {})
                    total_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
                    total_tx = sum(net.get('tx_bytes', 0) for net in networks.values())

                    # Block I/O
                    blkio_stats = stats.get('blkio_stats', {})
                    io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
                    total_read = sum(entry.get('value', 0) for entry in io_service_bytes if entry.get('op') == 'Read')
                    total_write = sum(entry.get('value', 0) for entry in io_service_bytes if entry.get('op') == 'Write')

                    # Container info
                    container_info = container.attrs
                    state = container_info.get('State', {})

                    stats_list.append({
                        "id": container.id[:12],
                        "name": container.name,
                        "status": container.status,
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_usage": memory_usage,
                        "memory_limit": memory_limit,
                        "memory_percent": round(memory_percent, 2),
                        "memory_mb": round(memory_usage / (1024**2), 2),
                        "memory_limit_mb": round(memory_limit / (1024**2), 2),
                        "network_rx_bytes": total_rx,
                        "network_tx_bytes": total_tx,
                        "network_rx_mb": round(total_rx / (1024**2), 2),
                        "network_tx_mb": round(total_tx / (1024**2), 2),
                        "block_read_bytes": total_read,
                        "block_write_bytes": total_write,
                        "block_read_mb": round(total_read / (1024**2), 2),
                        "block_write_mb": round(total_write / (1024**2), 2),
                        "pid": state.get('Pid'),
                        "started_at": state.get('StartedAt'),
                        "restart_count": container_info.get('RestartCount', 0),
                    })

                except Exception as e:
                    logger.error(f"Error getting stats for container {container.name}: {e}")

            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "container_count": len(stats_list),
                "containers": stats_list,
            }

        except Exception as e:
            logger.error(f"Error getting container stats: {e}")
            return {"status": "error", "error": str(e)}

    def get_container_health(self, container_name: str) -> Dict[str, Any]:
        """
        Get health status for a specific container.

        Args:
            container_name: Container name

        Returns:
            Dictionary with health status
        """
        if not self.is_available():
            return {"status": "error", "error": "Docker not available"}

        try:
            container = self.client.containers.get(container_name)
            container_info = container.attrs

            state = container_info.get('State', {})
            health = state.get('Health', {})

            return {
                "name": container.name,
                "status": container.status,
                "health_status": health.get('Status', 'none'),
                "running": state.get('Running', False),
                "paused": state.get('Paused', False),
                "restarting": state.get('Restarting', False),
                "oom_killed": state.get('OOMKilled', False),
                "dead": state.get('Dead', False),
                "exit_code": state.get('ExitCode', 0),
                "error": state.get('Error', ''),
                "started_at": state.get('StartedAt'),
                "finished_at": state.get('FinishedAt'),
                "restart_count": container_info.get('RestartCount', 0),
            }

        except NotFound:
            return {"status": "error", "error": f"Container {container_name} not found"}
        except Exception as e:
            logger.error(f"Error getting container health: {e}")
            return {"status": "error", "error": str(e)}

    def get_container_logs(
        self,
        container_name: str,
        tail: int = 100,
        since: Optional[str] = None
    ) -> List[str]:
        """
        Get container logs.

        Args:
            container_name: Container name
            tail: Number of lines to return
            since: Timestamp to start from

        Returns:
            List of log lines
        """
        if not self.is_available():
            return []

        try:
            container = self.client.containers.get(container_name)

            kwargs = {"tail": tail}
            if since:
                kwargs["since"] = since

            logs = container.logs(**kwargs).decode('utf-8').split('\n')
            return [line for line in logs if line]

        except NotFound:
            logger.error(f"Container {container_name} not found")
            return []
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return []

    def check_health(self) -> Dict[str, Any]:
        """
        Check overall Docker container health.

        Returns:
            Dictionary with health status and alerts
        """
        if not self.is_available():
            return {
                "status": "error",
                "error": "Docker not available",
                "alerts": ["Docker daemon is not accessible"],
            }

        try:
            alerts = []
            overall_status = "healthy"

            # Get all running containers
            containers = self.client.containers.list()
            stopped_containers = self.client.containers.list(filters={"status": "exited"})

            # Check for stopped containers
            if stopped_containers:
                alerts.append(f"{len(stopped_containers)} container(s) are stopped")
                overall_status = "warning"

            # Check resource usage
            for container in containers:
                try:
                    stats = container.stats(stream=False)

                    # CPU check
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                   stats['precpu_stats']['system_cpu_usage']
                    cpu_percent = 0.0
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * 100.0

                    if cpu_percent > self.CONTAINER_CPU_THRESHOLD:
                        alerts.append(f"Container {container.name} high CPU: {cpu_percent:.1f}%")
                        overall_status = "warning"

                    # Memory check
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 1)
                    memory_percent = (memory_usage / memory_limit) * 100

                    if memory_percent > self.CONTAINER_MEMORY_THRESHOLD:
                        alerts.append(f"Container {container.name} high memory: {memory_percent:.1f}%")
                        overall_status = "warning"

                    # Restart count check
                    restart_count = container.attrs.get('RestartCount', 0)
                    if restart_count > self.MAX_RESTARTS_PER_HOUR:
                        alerts.append(f"Container {container.name} restarted {restart_count} times")
                        overall_status = "warning"

                except Exception as e:
                    logger.error(f"Error checking container {container.name}: {e}")

            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "alerts": alerts,
                "summary": {
                    "running_containers": len(containers),
                    "stopped_containers": len(stopped_containers),
                    "total_containers": len(containers) + len(stopped_containers),
                }
            }

        except Exception as e:
            logger.error(f"Error checking Docker health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "alerts": ["Failed to check Docker health"],
            }
