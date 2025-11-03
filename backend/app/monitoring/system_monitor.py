"""
System Monitor

Monitors system resources: CPU, RAM, disk, network, processes.
"""

import psutil
import logging
from typing import Dict, Any, List
from datetime import datetime
import platform

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    System resource monitoring.

    Provides metrics for:
    - CPU usage (overall and per-core)
    - Memory usage (RAM)
    - Disk usage
    - Network I/O
    - Process count
    - System uptime
    """

    # Alert thresholds
    CPU_THRESHOLD = 85  # %
    RAM_THRESHOLD = 90  # %
    DISK_THRESHOLD = 85  # %

    @staticmethod
    def get_cpu_metrics() -> Dict[str, Any]:
        """
        Get CPU metrics.

        Returns:
            Dictionary with CPU metrics
        """
        try:
            # Overall CPU percentage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Per-core percentages
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # CPU count
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            # CPU frequency
            cpu_freq = psutil.cpu_freq()

            # CPU stats
            cpu_stats = psutil.cpu_stats()

            status = "healthy"
            if cpu_percent > SystemMonitor.CPU_THRESHOLD:
                status = "warning"
                logger.warning(f"High CPU usage: {cpu_percent}%")

            return {
                "status": status,
                "percent": round(cpu_percent, 2),
                "per_core": [round(p, 2) for p in cpu_per_core],
                "count_logical": cpu_count_logical,
                "count_physical": cpu_count_physical,
                "frequency": {
                    "current": round(cpu_freq.current, 2) if cpu_freq else None,
                    "min": round(cpu_freq.min, 2) if cpu_freq else None,
                    "max": round(cpu_freq.max, 2) if cpu_freq else None,
                },
                "stats": {
                    "ctx_switches": cpu_stats.ctx_switches,
                    "interrupts": cpu_stats.interrupts,
                    "soft_interrupts": cpu_stats.soft_interrupts,
                    "syscalls": cpu_stats.syscalls,
                }
            }

        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_memory_metrics() -> Dict[str, Any]:
        """
        Get memory (RAM) metrics.

        Returns:
            Dictionary with memory metrics
        """
        try:
            memory = psutil.virtual_memory()

            # Swap memory
            swap = psutil.swap_memory()

            status = "healthy"
            if memory.percent > SystemMonitor.RAM_THRESHOLD:
                status = "warning"
                logger.warning(f"High memory usage: {memory.percent}%")

            return {
                "status": status,
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": round(memory.percent, 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "percent": round(swap.percent, 2),
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                }
            }

        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_disk_metrics() -> Dict[str, Any]:
        """
        Get disk usage metrics.

        Returns:
            Dictionary with disk metrics
        """
        try:
            # Root partition
            disk_usage = psutil.disk_usage('/')

            # All partitions
            partitions = []
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": round(usage.percent, 2),
                    })
                except PermissionError:
                    continue

            # Disk I/O counters
            disk_io = psutil.disk_io_counters()

            status = "healthy"
            if disk_usage.percent > SystemMonitor.DISK_THRESHOLD:
                status = "warning"
                logger.warning(f"High disk usage: {disk_usage.percent}%")

            return {
                "status": status,
                "root": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": round(disk_usage.percent, 2),
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                },
                "partitions": partitions,
                "io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0,
                    "read_gb": round(disk_io.read_bytes / (1024**3), 2) if disk_io else 0,
                    "write_gb": round(disk_io.write_bytes / (1024**3), 2) if disk_io else 0,
                }
            }

        except Exception as e:
            logger.error(f"Error getting disk metrics: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_network_metrics() -> Dict[str, Any]:
        """
        Get network I/O metrics.

        Returns:
            Dictionary with network metrics
        """
        try:
            # Network I/O counters
            net_io = psutil.net_io_counters()

            # Per-interface stats
            interfaces = {}
            for interface, stats in psutil.net_io_counters(pernic=True).items():
                interfaces[interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout,
                    "mb_sent": round(stats.bytes_sent / (1024**2), 2),
                    "mb_recv": round(stats.bytes_recv / (1024**2), 2),
                }

            return {
                "status": "healthy",
                "total": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "mb_sent": round(net_io.bytes_sent / (1024**2), 2),
                    "mb_recv": round(net_io.bytes_recv / (1024**2), 2),
                    "gb_sent": round(net_io.bytes_sent / (1024**3), 2),
                    "gb_recv": round(net_io.bytes_recv / (1024**3), 2),
                },
                "interfaces": interfaces,
            }

        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_process_metrics() -> Dict[str, Any]:
        """
        Get process metrics.

        Returns:
            Dictionary with process metrics
        """
        try:
            # Process count
            process_count = len(psutil.pids())

            # Top processes by CPU
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage
            top_cpu = sorted(
                [p for p in processes if p['cpu_percent'] and p['cpu_percent'] > 0],
                key=lambda x: x['cpu_percent'],
                reverse=True
            )[:10]

            # Sort by memory usage
            top_memory = sorted(
                [p for p in processes if p['memory_percent'] and p['memory_percent'] > 0],
                key=lambda x: x['memory_percent'],
                reverse=True
            )[:10]

            return {
                "status": "healthy",
                "total_count": process_count,
                "top_cpu": [
                    {
                        "pid": p['pid'],
                        "name": p['name'],
                        "cpu_percent": round(p['cpu_percent'], 2)
                    }
                    for p in top_cpu
                ],
                "top_memory": [
                    {
                        "pid": p['pid'],
                        "name": p['name'],
                        "memory_percent": round(p['memory_percent'], 2)
                    }
                    for p in top_memory
                ],
            }

        except Exception as e:
            logger.error(f"Error getting process metrics: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get system information.

        Returns:
            Dictionary with system info
        """
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()

            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": round(uptime_seconds, 2),
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "uptime_days": round(uptime_seconds / 86400, 2),
            }

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_all_metrics() -> Dict[str, Any]:
        """
        Get all system metrics in a single call.

        Returns:
            Dictionary with all metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": SystemMonitor.get_system_info(),
            "cpu": SystemMonitor.get_cpu_metrics(),
            "memory": SystemMonitor.get_memory_metrics(),
            "disk": SystemMonitor.get_disk_metrics(),
            "network": SystemMonitor.get_network_metrics(),
            "processes": SystemMonitor.get_process_metrics(),
        }

    @staticmethod
    def check_health() -> Dict[str, Any]:
        """
        Check overall system health status.

        Returns:
            Dictionary with health status and alerts
        """
        alerts = []
        overall_status = "healthy"

        # Check CPU
        cpu = SystemMonitor.get_cpu_metrics()
        if cpu.get("status") == "warning":
            alerts.append(f"High CPU usage: {cpu.get('percent')}%")
            overall_status = "warning"

        # Check memory
        memory = SystemMonitor.get_memory_metrics()
        if memory.get("status") == "warning":
            alerts.append(f"High memory usage: {memory.get('percent')}%")
            overall_status = "warning"

        # Check disk
        disk = SystemMonitor.get_disk_metrics()
        if disk.get("status") == "warning":
            alerts.append(f"High disk usage: {disk.get('root', {}).get('percent')}%")
            overall_status = "warning"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": alerts,
            "summary": {
                "cpu_percent": cpu.get("percent"),
                "memory_percent": memory.get("percent"),
                "disk_percent": disk.get("root", {}).get("percent"),
            }
        }
