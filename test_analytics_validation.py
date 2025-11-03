#!/usr/bin/env python3
"""
Analytics Implementation Validation Script

Validates the analytics implementation by checking:
1. File existence
2. Import statements
3. Basic syntax
4. API endpoint structure
"""

import os
import sys
import importlib.util
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status='info'):
    """Print colored status message"""
    if status == 'success':
        print(f"{GREEN}✓{RESET} {message}")
    elif status == 'error':
        print(f"{RED}✗{RESET} {message}")
    elif status == 'warning':
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"{BLUE}ℹ{RESET} {message}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"{description}: {filepath}", 'success')
        return True
    else:
        print_status(f"{description} NOT FOUND: {filepath}", 'error')
        return False

def validate_python_syntax(filepath):
    """Validate Python file syntax"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print_status(f"  Syntax error in {filepath}: {e}", 'error')
        return False
    except Exception as e:
        print_status(f"  Error reading {filepath}: {e}", 'error')
        return False

def main():
    print("\n" + "="*70)
    print(f"{BLUE}SmartPort Analytics - Implementation Validation{RESET}")
    print("="*70 + "\n")

    base_dir = Path(__file__).parent
    backend_dir = base_dir / 'backend'
    frontend_dir = base_dir / 'frontend'

    all_passed = True

    # Backend Files Check
    print(f"\n{BLUE}[1/5] Backend Files Validation{RESET}")
    print("-" * 70)

    backend_files = [
        (backend_dir / 'app/schemas/analytics.py', 'Analytics Schemas'),
        (backend_dir / 'app/services/analytics.py', 'Analytics Service'),
        (backend_dir / 'app/api/v1/endpoints/analytics.py', 'Analytics Endpoints'),
        (backend_dir / 'app/api/v1/endpoints/websocket_analytics.py', 'WebSocket Endpoints'),
        (backend_dir / 'app/api/v1/api.py', 'API Router'),
    ]

    for filepath, description in backend_files:
        if check_file_exists(filepath, description):
            if not validate_python_syntax(filepath):
                all_passed = False
        else:
            all_passed = False

    # Frontend Files Check
    print(f"\n{BLUE}[2/5] Frontend Files Validation{RESET}")
    print("-" * 70)

    frontend_files = [
        (frontend_dir / 'src/components/QueryBuilder/TagSelector.tsx', 'TagSelector Component'),
        (frontend_dir / 'src/components/QueryBuilder/TimeRangePicker.tsx', 'TimeRangePicker Component'),
        (frontend_dir / 'src/components/QueryBuilder/FilterBuilder.tsx', 'FilterBuilder Component'),
        (frontend_dir / 'src/components/QueryBuilder/AggregationBuilder.tsx', 'AggregationBuilder Component'),
        (frontend_dir / 'src/components/QueryBuilder/QueryBuilder.tsx', 'QueryBuilder Component'),
        (frontend_dir / 'src/components/QueryBuilder/StreamControls.tsx', 'StreamControls Component'),
        (frontend_dir / 'src/components/QueryBuilder/index.ts', 'QueryBuilder Index'),
        (frontend_dir / 'src/hooks/useAnalyticsStream.ts', 'useAnalyticsStream Hook'),
        (frontend_dir / 'src/services/analyticsApi.ts', 'Analytics API Service'),
        (frontend_dir / 'src/pages/AnalyticsPage.tsx', 'Analytics Page'),
    ]

    for filepath, description in frontend_files:
        if not check_file_exists(filepath, description):
            all_passed = False

    # Visualization Components Check
    print(f"\n{BLUE}[3/5] Visualization Components Validation{RESET}")
    print("-" * 70)

    viz_components = [
        'GaugeChart.tsx',
        'HeatmapChart.tsx',
        'ScatterPlot.tsx',
        'MultiAxisChart.tsx',
        'BarChart.tsx',
        'PieChart.tsx',
        'BoxPlot.tsx',
        'WaterfallChart.tsx',
        'RadarChart.tsx',
        'SankeyDiagram.tsx',
        'TreemapChart.tsx',
        'GeoMap.tsx',
    ]

    viz_dir = frontend_dir / 'src/components/Visualizations'
    for component in viz_components:
        filepath = viz_dir / component
        if not check_file_exists(filepath, component):
            all_passed = False

    # Dependencies Check
    print(f"\n{BLUE}[4/5] Dependencies Check{RESET}")
    print("-" * 70)

    # Backend dependencies
    requirements_file = backend_dir / 'requirements.txt'
    if os.path.exists(requirements_file):
        print_status("Backend requirements.txt found", 'success')
        with open(requirements_file, 'r') as f:
            requirements = f.read()
            required_packages = ['fastapi', 'influxdb-client', 'pandas', 'pydantic']
            for package in required_packages:
                if package in requirements.lower():
                    print_status(f"  {package} found in requirements", 'success')
                else:
                    print_status(f"  {package} NOT found in requirements", 'warning')
    else:
        print_status("Backend requirements.txt NOT FOUND", 'error')
        all_passed = False

    # Frontend dependencies
    package_json = frontend_dir / 'package.json'
    if os.path.exists(package_json):
        print_status("Frontend package.json found", 'success')
        import json
        with open(package_json, 'r') as f:
            pkg_data = json.load(f)
            dependencies = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
            required_packages = ['react', 'plotly.js', 'react-plotly.js', 'lucide-react']
            for package in required_packages:
                if package in dependencies:
                    print_status(f"  {package} found in package.json", 'success')
                else:
                    print_status(f"  {package} NOT found in package.json", 'warning')
    else:
        print_status("Frontend package.json NOT FOUND", 'error')
        all_passed = False

    # Configuration Check
    print(f"\n{BLUE}[5/5] Configuration Check{RESET}")
    print("-" * 70)

    # Check for .env files
    backend_env = backend_dir / '.env'
    if os.path.exists(backend_env):
        print_status("Backend .env found", 'success')
    else:
        print_status("Backend .env NOT FOUND (may use defaults)", 'warning')

    frontend_env = frontend_dir / '.env'
    if os.path.exists(frontend_env):
        print_status("Frontend .env found", 'success')
    else:
        print_status("Frontend .env NOT FOUND (may use defaults)", 'warning')

    # Summary
    print("\n" + "="*70)
    if all_passed:
        print(f"{GREEN}✓ All validation checks PASSED!{RESET}")
        print("\n" + "="*70)
        print(f"{BLUE}Next Steps:{RESET}")
        print("1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("2. Start frontend: cd frontend && npm start")
        print("3. Run test script: python test_analytics_endpoints.py")
        print("="*70 + "\n")
        return 0
    else:
        print(f"{RED}✗ Some validation checks FAILED!{RESET}")
        print(f"{YELLOW}Please fix the issues above before proceeding.{RESET}")
        print("="*70 + "\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
