"""
Auto Dashboard Generator

Automatically generates dashboards based on asset types and operational data.
Uses AI to intelligently select relevant widgets and metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.asset import Asset

logger = logging.getLogger(__name__)


class AutoDashboardGenerator:
    """
    Automatically generates dashboards based on asset type and context.

    Creates intelligent dashboards with:
    - Appropriate widgets for asset type
    - Relevant metrics and KPIs
    - Logical layout and grouping
    """

    # Dashboard templates by asset type
    DASHBOARD_TEMPLATES = {
        "shiploader": {
            "name": "Shiploader Dashboard",
            "description": "Real-time monitoring of grain shiploader operations",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Belt Speed",
                    "metric": "belt_speed",
                    "unit": "m/s",
                    "min": 0,
                    "max": 5,
                    "thresholds": {"low": 1, "high": 4},
                },
                {
                    "type": "gauge",
                    "title": "Load Weight",
                    "metric": "load_weight",
                    "unit": "kg",
                    "min": 0,
                    "max": 10000,
                },
                {
                    "type": "linechart",
                    "title": "Loading Rate",
                    "metric": "loading_rate",
                    "unit": "tons/hour",
                    "timeRange": "1h",
                },
                {
                    "type": "barchart",
                    "title": "Hourly Tonnage",
                    "metric": "hourly_tonnage",
                    "unit": "tons",
                },
                {
                    "type": "status",
                    "title": "Operational Status",
                    "metric": "operational_status",
                },
                {
                    "type": "counter",
                    "title": "Total Loaded Today",
                    "metric": "daily_tonnage",
                    "unit": "tons",
                },
                {
                    "type": "alarmlist",
                    "title": "Active Alarms",
                    "limit": 10,
                },
            ],
        },
        "silo": {
            "name": "Silo Monitoring Dashboard",
            "description": "Silo storage monitoring and management",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Level",
                    "metric": "level",
                    "unit": "%",
                    "min": 0,
                    "max": 100,
                    "thresholds": {"low": 20, "high": 90},
                },
                {
                    "type": "gauge",
                    "title": "Temperature",
                    "metric": "temperature",
                    "unit": "°C",
                    "min": -10,
                    "max": 60,
                    "thresholds": {"low": 10, "high": 40},
                },
                {
                    "type": "gauge",
                    "title": "Moisture",
                    "metric": "moisture",
                    "unit": "%",
                    "min": 0,
                    "max": 30,
                    "thresholds": {"low": 10, "high": 20},
                },
                {
                    "type": "linechart",
                    "title": "Level Trend",
                    "metric": "level",
                    "unit": "%",
                    "timeRange": "24h",
                },
                {
                    "type": "linechart",
                    "title": "Temperature Trend",
                    "metric": "temperature",
                    "unit": "°C",
                    "timeRange": "24h",
                },
                {
                    "type": "counter",
                    "title": "Current Volume",
                    "metric": "current_volume",
                    "unit": "m³",
                },
                {
                    "type": "status",
                    "title": "Product Type",
                    "metric": "product_type",
                },
            ],
        },
        "conveyor": {
            "name": "Conveyor System Dashboard",
            "description": "Belt conveyor monitoring and performance",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Belt Speed",
                    "metric": "belt_speed",
                    "unit": "m/s",
                    "min": 0,
                    "max": 3,
                },
                {
                    "type": "gauge",
                    "title": "Motor Current",
                    "metric": "motor_current",
                    "unit": "A",
                    "min": 0,
                    "max": 100,
                    "thresholds": {"low": 20, "high": 80},
                },
                {
                    "type": "gauge",
                    "title": "Bearing Temperature",
                    "metric": "bearing_temp",
                    "unit": "°C",
                    "min": 0,
                    "max": 100,
                    "thresholds": {"low": 40, "high": 70},
                },
                {
                    "type": "linechart",
                    "title": "Speed Trend",
                    "metric": "belt_speed",
                    "unit": "m/s",
                    "timeRange": "1h",
                },
                {
                    "type": "linechart",
                    "title": "Current Trend",
                    "metric": "motor_current",
                    "unit": "A",
                    "timeRange": "1h",
                },
                {
                    "type": "status",
                    "title": "Running Status",
                    "metric": "running_status",
                },
                {
                    "type": "counter",
                    "title": "Running Hours Today",
                    "metric": "daily_running_hours",
                    "unit": "h",
                },
            ],
        },
        "weighbridge": {
            "name": "Weighbridge Dashboard",
            "description": "Truck weighing operations monitoring",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Current Weight",
                    "metric": "current_weight",
                    "unit": "kg",
                    "min": 0,
                    "max": 80000,
                },
                {
                    "type": "counter",
                    "title": "Trucks Today",
                    "metric": "trucks_today",
                },
                {
                    "type": "counter",
                    "title": "Total Tonnage Today",
                    "metric": "tonnage_today",
                    "unit": "tons",
                },
                {
                    "type": "barchart",
                    "title": "Hourly Trucks",
                    "metric": "hourly_truck_count",
                },
                {
                    "type": "piechart",
                    "title": "Product Distribution",
                    "metric": "product_distribution",
                },
                {
                    "type": "status",
                    "title": "Status",
                    "metric": "weighbridge_status",
                },
                {
                    "type": "linechart",
                    "title": "Average Wait Time",
                    "metric": "avg_wait_time",
                    "unit": "min",
                    "timeRange": "8h",
                },
            ],
        },
        "motor": {
            "name": "Motor Dashboard",
            "description": "Electric motor monitoring and diagnostics",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Current",
                    "metric": "current",
                    "unit": "A",
                    "min": 0,
                    "max": 200,
                    "thresholds": {"low": 50, "high": 180},
                },
                {
                    "type": "gauge",
                    "title": "Voltage",
                    "metric": "voltage",
                    "unit": "V",
                    "min": 0,
                    "max": 500,
                    "thresholds": {"low": 380, "high": 420},
                },
                {
                    "type": "gauge",
                    "title": "Temperature",
                    "metric": "temperature",
                    "unit": "°C",
                    "min": 0,
                    "max": 120,
                    "thresholds": {"low": 60, "high": 90},
                },
                {
                    "type": "gauge",
                    "title": "Vibration",
                    "metric": "vibration",
                    "unit": "mm/s",
                    "min": 0,
                    "max": 10,
                    "thresholds": {"low": 2, "high": 7},
                },
                {
                    "type": "linechart",
                    "title": "Power Consumption",
                    "metric": "power",
                    "unit": "kW",
                    "timeRange": "24h",
                },
                {
                    "type": "status",
                    "title": "Running Status",
                    "metric": "running_status",
                },
                {
                    "type": "counter",
                    "title": "Running Hours",
                    "metric": "total_running_hours",
                    "unit": "h",
                },
            ],
        },
        "pump": {
            "name": "Pump Dashboard",
            "description": "Pump system monitoring",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Flow Rate",
                    "metric": "flow_rate",
                    "unit": "m³/h",
                    "min": 0,
                    "max": 100,
                },
                {
                    "type": "gauge",
                    "title": "Discharge Pressure",
                    "metric": "discharge_pressure",
                    "unit": "bar",
                    "min": 0,
                    "max": 10,
                },
                {
                    "type": "gauge",
                    "title": "Suction Pressure",
                    "metric": "suction_pressure",
                    "unit": "bar",
                    "min": -1,
                    "max": 2,
                },
                {
                    "type": "gauge",
                    "title": "Motor Current",
                    "metric": "motor_current",
                    "unit": "A",
                    "min": 0,
                    "max": 50,
                },
                {
                    "type": "linechart",
                    "title": "Flow Rate Trend",
                    "metric": "flow_rate",
                    "unit": "m³/h",
                    "timeRange": "8h",
                },
                {
                    "type": "status",
                    "title": "Running Status",
                    "metric": "running_status",
                },
            ],
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_dashboard(self, asset_id: str) -> Dict[str, Any]:
        """
        Generate a dashboard for a specific asset.

        Args:
            asset_id: Asset ID

        Returns:
            Dashboard configuration
        """
        try:
            # Get asset
            result = await self.db.execute(
                select(Asset).where(Asset.id == asset_id)
            )
            asset = result.scalar_one_or_none()

            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Get dashboard template for asset type
            asset_type = asset.asset_type.lower() if asset.asset_type else "generic"

            template = self.DASHBOARD_TEMPLATES.get(
                asset_type,
                self._generate_generic_dashboard(asset)
            )

            # Customize dashboard with asset-specific information
            dashboard = {
                "id": f"dashboard_{asset_id}_{int(datetime.now().timestamp())}",
                "asset_id": asset_id,
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "name": f"{asset.name} - {template['name']}",
                "description": template.get('description', ''),
                "widgets": template.get('widgets', []),
                "layout": self._generate_layout(len(template.get('widgets', []))),
                "created_at": datetime.utcnow().isoformat(),
                "auto_generated": True,
            }

            logger.info(f"Generated dashboard for asset {asset_id} ({asset_type})")

            return dashboard

        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            raise

    def _generate_generic_dashboard(self, asset: Asset) -> Dict[str, Any]:
        """Generate a generic dashboard for unknown asset types."""
        return {
            "name": "Asset Dashboard",
            "description": f"Monitoring dashboard for {asset.name}",
            "widgets": [
                {
                    "type": "gauge",
                    "title": "Health Score",
                    "metric": "health_score",
                    "unit": "%",
                    "min": 0,
                    "max": 100,
                    "thresholds": {"low": 60, "high": 80},
                },
                {
                    "type": "status",
                    "title": "Status",
                    "metric": "status",
                },
                {
                    "type": "counter",
                    "title": "Active Alerts",
                    "metric": "active_alerts",
                },
                {
                    "type": "alarmlist",
                    "title": "Recent Alarms",
                    "limit": 5,
                },
            ],
        }

    def _generate_layout(self, widget_count: int) -> List[Dict[str, int]]:
        """
        Generate a responsive grid layout for widgets.

        Args:
            widget_count: Number of widgets

        Returns:
            List of layout configurations (x, y, w, h)
        """
        layout = []
        cols = 12  # Grid columns

        # Define widget sizes
        if widget_count <= 3:
            # Few widgets - make them larger
            width = cols // widget_count
            for i in range(widget_count):
                layout.append({
                    "x": i * width,
                    "y": 0,
                    "w": width,
                    "h": 4,
                })
        elif widget_count <= 6:
            # Medium number - 2 rows
            width = cols // 3
            for i in range(widget_count):
                row = i // 3
                col = i % 3
                layout.append({
                    "x": col * width,
                    "y": row * 4,
                    "w": width,
                    "h": 4,
                })
        else:
            # Many widgets - 3 columns
            width = cols // 3
            for i in range(widget_count):
                row = i // 3
                col = i % 3
                layout.append({
                    "x": col * width,
                    "y": row * 3,
                    "w": width,
                    "h": 3,
                })

        return layout

    async def generate_dashboards_for_site(self, site_id: int) -> List[Dict[str, Any]]:
        """
        Generate dashboards for all assets in a site.

        Args:
            site_id: Site ID

        Returns:
            List of dashboard configurations
        """
        try:
            # Get all assets for site
            result = await self.db.execute(
                select(Asset).where(Asset.site_id == site_id)
            )
            assets = result.scalars().all()

            dashboards = []
            for asset in assets:
                try:
                    dashboard = await self.generate_dashboard(str(asset.id))
                    dashboards.append(dashboard)
                except Exception as e:
                    logger.error(f"Error generating dashboard for asset {asset.id}: {e}")

            logger.info(f"Generated {len(dashboards)} dashboards for site {site_id}")

            return dashboards

        except Exception as e:
            logger.error(f"Error generating dashboards for site: {e}")
            raise

    def get_available_templates(self) -> Dict[str, str]:
        """
        Get list of available dashboard templates.

        Returns:
            Dict of template names and descriptions
        """
        return {
            asset_type: template.get('name', asset_type)
            for asset_type, template in self.DASHBOARD_TEMPLATES.items()
        }
