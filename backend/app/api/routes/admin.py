"""
Admin routes for system monitoring
"""
from typing import Dict, List, Any
from fastapi import APIRouter
import psutil
import subprocess
import json
from datetime import datetime

router = APIRouter()


@router.get("/system/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """
    Get system resource metrics (CPU, memory, disk)
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / (1024 ** 2)
        memory_total_mb = memory.total / (1024 ** 2)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        uptime_hours = uptime_seconds / 3600
        
        return {
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory_used_mb,
            "memory_total_mb": memory_total_mb,
            "memory_percent": memory.percent,
            "disk_used_gb": disk_used_gb,
            "disk_total_gb": disk_total_gb,
            "disk_percent": disk.percent,
            "uptime_hours": uptime_hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "cpu_percent": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 0,
            "disk_used_gb": 0,
            "disk_total_gb": 0,
            "uptime_hours": 0
        }


@router.get("/docker/containers", response_model=List[Dict[str, Any]])
async def get_docker_containers():
    """
    Get Docker container status using raw Unix socket communication
    Pure Python implementation to avoid urllib3 conflicts
    """
    try:
        import socket
        import json
        from datetime import datetime
        
        # Create Unix socket connection
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect('/var/run/docker.sock')
        
        # Send HTTP GET request to Docker API
        request = b'GET /containers/json?all=1 HTTP/1.1\r\nHost: localhost\r\n\r\n'
        sock.sendall(request)
        
        # Receive response
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            # Check if we have complete response (look for end of JSON)
            if b'\r\n\r\n' in response_data and response_data.rstrip().endswith(b']'):
                break
        
        sock.close()
        
        # Parse HTTP response
        response_str = response_data.decode('utf-8')
        
        # Split headers and body
        parts = response_str.split('\r\n\r\n', 1)
        if len(parts) < 2:
            raise Exception("Invalid HTTP response")
        
        body = parts[1]
        
        # Parse JSON
        containers_data = json.loads(body)
        containers = []
        
        for container in containers_data:
            # Extract container info
            container_id = container.get('Id', '')[:12]
            name = container.get('Names', ['unknown'])[0].lstrip('/')
            image = container.get('Image', 'unknown')
            state = container.get('State', 'unknown')
            status = container.get('Status', 'unknown')
            
            # Get health status
            health = 'unknown'
            if state == 'running':
                health_info = container.get('Status', '')
                if 'healthy' in health_info.lower():
                    health = 'healthy'
                elif 'unhealthy' in health_info.lower():
                    health = 'unhealthy'
                elif 'starting' in health_info.lower():
                    health = 'starting'
                else:
                    health = 'running'
            elif state == 'exited':
                health = 'stopped'
            else:
                health = state
            
            # Format status
            status_str = state.capitalize()
            if health == 'healthy':
                status_str += ' (healthy)'
            elif health == 'unhealthy':
                status_str += ' (unhealthy)'
            elif health == 'starting':
                status_str += ' (starting)'
            
            # Get ports
            ports_list = []
            ports_data = container.get('Ports', [])
            for port in ports_data:
                if port.get('PublicPort'):
                    ports_list.append(f"{port['PublicPort']}:{port.get('PrivatePort', '?')}")
                elif port.get('PrivatePort'):
                    ports_list.append(str(port['PrivatePort']))
            ports = ', '.join(ports_list) if ports_list else 'N/A'
            
            # Calculate creation time
            created_timestamp = container.get('Created', 0)
            created_str = "unknown"
            try:
                created_dt = datetime.fromtimestamp(created_timestamp)
                now = datetime.now()
                delta = now - created_dt
                
                if delta.days > 0:
                    created_str = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
                elif delta.seconds > 3600:
                    hours = delta.seconds // 3600
                    created_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif delta.seconds > 60:
                    minutes = delta.seconds // 60
                    created_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    created_str = "just now"
            except:
                pass
            
            containers.append({
                'id': container_id,
                'name': name,
                'image': image,
                'status': status_str,
                'health': health,
                'ports': ports,
                'created': created_str,
            })
        
        return containers
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        # Return error info
        return [{
            'id': 'error',
            'name': 'Docker API Error',
            'image': error_detail[:300],
            'status': 'error',
            'health': 'unhealthy',
            'ports': 'N/A',
            'created': 'N/A',
        }]


@router.get("/docker/stats", response_model=Dict[str, Any])
async def get_docker_stats(container_name: str):
    """
    Get Docker container resource usage stats
    """
    try:
        result = subprocess.run(
            ['docker', 'stats', container_name, '--no-stream', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"error": "Container not found"}
        
        stats = json.loads(result.stdout.strip())
        return {
            'name': stats.get('Name', ''),
            'cpu_percent': stats.get('CPUPerc', '0%').replace('%', ''),
            'memory_usage': stats.get('MemUsage', ''),
            'memory_percent': stats.get('MemPerc', '0%').replace('%', ''),
            'net_io': stats.get('NetIO', ''),
            'block_io': stats.get('BlockIO', ''),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/services/health", response_model=List[Dict[str, Any]])
async def get_services_health():
    """
    Get health status of all services
    """
    import requests
    import socket
    
    services = [
        {"name": "Backend API", "url": "http://localhost:8000/health", "type": "http", "host": "localhost", "port": 8000},
        {"name": "Frontend", "url": "http://localhost:3000", "type": "http", "host": "localhost", "port": 3000},
        {"name": "PostgreSQL", "url": "localhost:5432", "type": "tcp", "host": "postgres", "port": 5432},
        {"name": "InfluxDB", "url": "http://localhost:8086/health", "type": "http", "host": "localhost", "port": 8086},
        {"name": "Redis", "url": "localhost:6379", "type": "tcp", "host": "redis", "port": 6379},
        {"name": "RabbitMQ", "url": "http://localhost:15672", "type": "http", "host": "localhost", "port": 15672},
        {"name": "Grafana", "url": "http://localhost:3001", "type": "http", "host": "localhost", "port": 3001},
        {"name": "Prometheus", "url": "http://localhost:9090", "type": "http", "host": "localhost", "port": 9090},
    ]
    
    # Check each service
    for service in services:
        try:
            if service["type"] == "http":
                response = requests.get(service["url"], timeout=2)
                service["status"] = "healthy" if response.status_code < 500 else "unhealthy"
            elif service["type"] == "tcp":
                # Check TCP port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((service["host"], service["port"]))
                sock.close()
                service["status"] = "healthy" if result == 0 else "unhealthy"
        except Exception as e:
            service["status"] = "unhealthy"
    
    return services


@router.get("/gpu/info", response_model=Dict[str, Any])
async def get_gpu_info():
    """
    Get GPU information using nvidia-smi
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version,memory.total,memory.free,memory.used,utilization.gpu,utilization.memory,temperature.gpu', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"available": False}
        
        # Parse output
        data = result.stdout.strip().split(',')
        if len(data) >= 8:
            return {
                "available": True,
                "name": data[0].strip(),
                "driver_version": data[1].strip(),
                "memory_total_mb": float(data[2].strip().replace(' MiB', '')),
                "memory_free_mb": float(data[3].strip().replace(' MiB', '')),
                "memory_used_mb": float(data[4].strip().replace(' MiB', '')),
                "utilization_gpu": float(data[5].strip().replace(' %', '')),
                "utilization_memory": float(data[6].strip().replace(' %', '')),
                "temperature": float(data[7].strip()),
            }
        else:
            return {"available": False}
    except Exception as e:
        return {"available": False, "error": str(e)}
