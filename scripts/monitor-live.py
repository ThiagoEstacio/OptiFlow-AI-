#!/usr/bin/env python3
"""
OptiFlow AI - Real-time Container Monitor
Monitora containers com atualização em tempo real
"""
import subprocess
import json
import time
import sys
from datetime import datetime

# Cores ANSI
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

def clear_screen():
    """Limpa a tela"""
    print('\033[2J\033[H', end='')

def get_container_stats():
    """Obtém estatísticas dos containers"""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
        return containers
    except Exception as e:
        print(f"{Colors.RED}Erro ao obter status dos containers: {e}{Colors.NC}")
        return []

def get_container_resource_usage(name):
    """Obtém uso de CPU e memória de um container"""
    try:
        result = subprocess.run(
            ['docker', 'stats', name, '--no-stream', '--format', 
             '{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}'],
            capture_output=True,
            text=True,
            check=True
        )
        parts = result.stdout.strip().split('|')
        if len(parts) >= 3:
            return {
                'cpu': parts[0],
                'mem': parts[1].split('/')[0].strip(),
                'network': parts[2].split('/')[0].strip()
            }
    except:
        pass
    return {'cpu': 'N/A', 'mem': 'N/A', 'network': 'N/A'}

def format_status(state, health):
    """Formata status com cores"""
    if state != 'running':
        return f"{Colors.RED}●{Colors.NC} {state}"
    
    if health == 'healthy':
        return f"{Colors.GREEN}●{Colors.NC} healthy"
    elif health == 'unhealthy':
        return f"{Colors.RED}●{Colors.NC} unhealthy"
    elif health == 'starting':
        return f"{Colors.YELLOW}●{Colors.NC} starting"
    else:
        return f"{Colors.GREEN}●{Colors.NC} running"

def print_header():
    """Imprime cabeçalho"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.BLUE}{'='*80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.CYAN}OptiFlow AI - Container Monitor{Colors.NC} | {now}")
    print(f"{Colors.BLUE}{'='*80}{Colors.NC}\n")

def print_container_group(title, containers):
    """Imprime grupo de containers"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}{title}{Colors.NC}")
    print(f"{Colors.BLUE}{'-'*80}{Colors.NC}")
    
    for container in containers:
        name = container.get('Service', 'unknown')
        state = container.get('State', 'unknown')
        health = container.get('Health', 'none')
        
        # Get resource usage
        container_name = container.get('Name', '')
        resources = get_container_resource_usage(container_name)
        
        status_str = format_status(state, health)
        
        print(f"  {status_str:20} {name:25} CPU: {resources['cpu']:8} MEM: {resources['mem']:10}")
    
    print()

def monitor_once():
    """Executa uma iteração de monitoramento"""
    clear_screen()
    print_header()
    
    containers = get_container_stats()
    
    if not containers:
        print(f"{Colors.RED}Nenhum container encontrado ou erro ao listar{Colors.NC}")
        return
    
    # Agrupar containers por categoria
    core = [c for c in containers if c.get('Service') in ['backend', 'frontend', 'gateway']]
    infra = [c for c in containers if c.get('Service') in ['postgres', 'redis', 'influxdb']]
    messaging = [c for c in containers if c.get('Service') in ['kafka', 'zookeeper', 'rabbitmq', 'kafka-ui']]
    jobs = [c for c in containers if c.get('Service') in ['celery-worker', 'celery-beat']]
    monitoring = [c for c in containers if c.get('Service') in [
        'prometheus', 'grafana', 'node-exporter', 'cadvisor', 
        'postgres-exporter', 'redis-exporter'
    ]]
    simulation = [c for c in containers if c.get('Service') in ['opcua-server', 'mlflow']]
    
    # Imprimir grupos
    if core:
        print_container_group("🚀 Core Application", core)
    if infra:
        print_container_group("🗄️  Infrastructure", infra)
    if messaging:
        print_container_group("📨 Messaging", messaging)
    if jobs:
        print_container_group("⚙️  Background Jobs", jobs)
    if monitoring:
        print_container_group("📊 Monitoring", monitoring)
    if simulation:
        print_container_group("🧪 Simulation & ML", simulation)
    
    # Summary
    total = len(containers)
    running = sum(1 for c in containers if c.get('State') == 'running')
    healthy = sum(1 for c in containers if c.get('Health') == 'healthy')
    unhealthy = sum(1 for c in containers if c.get('Health') in ['unhealthy', 'starting'])
    
    print(f"{Colors.BLUE}{'='*80}{Colors.NC}")
    print(f"📈 {Colors.BOLD}Summary:{Colors.NC} ", end='')
    print(f"Total: {Colors.CYAN}{total}{Colors.NC} | ", end='')
    print(f"Running: {Colors.GREEN}{running}{Colors.NC} | ", end='')
    print(f"Healthy: {Colors.GREEN}{healthy}{Colors.NC}", end='')
    if unhealthy > 0:
        print(f" | Unhealthy: {Colors.RED}{unhealthy}{Colors.NC}", end='')
    print()
    
    print(f"\n{Colors.YELLOW}Press Ctrl+C to exit | Refreshing every 5 seconds...{Colors.NC}")

def monitor_continuous():
    """Monitora continuamente"""
    try:
        while True:
            monitor_once()
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}Monitor stopped by user{Colors.NC}")
        sys.exit(0)

def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor_continuous()
    else:
        monitor_once()

if __name__ == '__main__':
    main()
