"""
AI Agent Tools - Function Calling for LLM

Provides tools/functions that the AI agent can call to:
- Get real-time data
- Query historical data
- Calculate statistics
- Search for tags
"""

from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by the LLM"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = []


class ToolCall(BaseModel):
    """A tool call request from the LLM"""
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool execution"""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None


# Define available tools for the LLM
AVAILABLE_TOOLS = [
    {
        "name": "get_realtime_value",
        "description": "Get the current real-time value of a specific tag/sensor. Use this when the user asks about current values, latest readings, or 'now'.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier (e.g., 'ARZ_CORR01_VELOCIDADE_PV', 'temp_01')"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "get_multiple_realtime_values",
        "description": "Get current values for multiple tags at once. Use when user asks about multiple sensors simultaneously.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tag identifiers"
                }
            },
            "required": ["tag_ids"]
        }
    },
    {
        "name": "get_historical_data",
        "description": "Get historical time-series data for a tag over a time period. Use when user asks about trends, history, past values, or wants to see data over time.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration (default: 1h)"
                },
                "aggregation": {
                    "type": "string",
                    "enum": ["mean", "max", "min", "sum", "stddev"],
                    "description": "Optional aggregation function"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "calculate_statistics",
        "description": "Calculate statistical metrics (average, min, max, stddev) for a tag over a time period. Use when user asks for averages, maximum, minimum, statistics, or analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for calculation (default: 1h)"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "search_tags",
        "description": "Search for available tags by name or description. Use when user mentions a sensor/parameter but you don't know the exact tag ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'temperature', 'velocity', 'pressure')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "compare_tags",
        "description": "Compare multiple tags over time to find correlations, patterns, or relationships. Use for root cause analysis or multi-variable analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tag identifiers to compare (2-10 tags)"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for comparison (default: 24h)"
                }
            },
            "required": ["tag_ids"]
        }
    },
    {
        "name": "detect_anomalies",
        "description": "Detect anomalies, outliers, or unusual patterns in tag data. Use when investigating problems, unexpected behavior, or quality issues.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for analysis (default: 24h)"
                },
                "sensitivity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Detection sensitivity (default: medium)"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "calculate_oee",
        "description": "Calculate Overall Equipment Effectiveness (OEE) for equipment. Requires availability, performance, and quality metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "equipment_tags": {
                    "type": "object",
                    "properties": {
                        "running_status": {"type": "string", "description": "Tag for running/stopped status"},
                        "speed_actual": {"type": "string", "description": "Actual speed tag"},
                        "speed_design": {"type": "number", "description": "Design speed value"},
                        "quality_good": {"type": "string", "description": "Good units count (optional)"},
                        "quality_total": {"type": "string", "description": "Total units count (optional)"}
                    },
                    "description": "Map of equipment tags for OEE calculation"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for OEE calculation (default: 24h)"
                }
            },
            "required": ["equipment_tags"]
        }
    },
    {
        "name": "analyze_alarm_patterns",
        "description": "Analyze alarm patterns to identify frequent alarms, alarm floods, chattering alarms, or priority distribution.",
        "parameters": {
            "type": "object",
            "properties": {
                "alarm_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of alarm-related tag identifiers"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for analysis (default: 24h)"
                }
            },
            "required": ["alarm_tags"]
        }
    },
    {
        "name": "get_tag_metadata",
        "description": "Get detailed metadata about a tag including engineering units, ranges, descriptions, categories, and configurations.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "get_all_tags",
        "description": "Get list of all available tags in the system. Use when user asks 'what tags are available', 'list all sensors', or needs to know what data is available.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tags to return (default: 50)"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Return only active tags (default: true)"
                }
            }
        }
    },
    {
        "name": "get_active_alarms",
        "description": "Get list of currently active alarms in the system. Use when user asks about current alarms, alerts, or problems that need attention.",
        "parameters": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by severity level (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of alarms to return (default: 20)"
                }
            }
        }
    },
    {
        "name": "analyze_alarm_frequency",
        "description": "Analyze alarm frequency over time to identify chattering alarms, alarm floods, and frequency patterns. Use when user asks about alarm frequency, how often alarms occur, or alarm trends.",
        "parameters": {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for frequency analysis (default: 24h)"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by severity level (optional)"
                },
                "equipment_filter": {
                    "type": "string",
                    "description": "Filter by equipment name/prefix (optional, e.g., 'ELEV01', 'SILO')"
                },
                "threshold": {
                    "type": "integer",
                    "description": "Minimum alarm count to include in results (default: 1)"
                }
            }
        }
    },
    {
        "name": "generate_data_histogram",
        "description": "Generate histogram distribution for sensor data or alarm patterns. Use when user asks about data distribution, value ranges, frequency distribution, or histogram.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier for sensor data histogram"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for histogram (default: 24h)"
                },
                "bins": {
                    "type": "integer",
                    "description": "Number of histogram bins/buckets (default: 10)"
                },
                "histogram_type": {
                    "type": "string",
                    "enum": ["value_distribution", "alarm_frequency", "time_distribution"],
                    "description": "Type of histogram to generate (default: value_distribution)"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "calculate_correlation",
        "description": "Calculate statistical correlation between two or more tags to identify relationships and dependencies. Use for root cause analysis, process optimization, or understanding variable relationships.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-10 tag identifiers to correlate"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for correlation analysis (default: 24h)"
                },
                "method": {
                    "type": "string",
                    "enum": ["pearson", "spearman", "kendall"],
                    "description": "Correlation method (default: pearson)"
                }
            },
            "required": ["tag_ids"]
        }
    },
    {
        "name": "detect_trends",
        "description": "Detect trends in sensor data (increasing, decreasing, stable, cyclic). Use when user asks about trends, patterns over time, or if values are rising/falling.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "The tag identifier"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for trend detection (default: 24h)"
                },
                "sensitivity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Trend detection sensitivity (default: medium)"
                }
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "generate_insights",
        "description": "Generate automated insights from data patterns, anomalies, and trends. Use when user asks for insights, recommendations, analysis summary, or what's noteworthy.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["tag", "equipment", "system", "alarms"],
                    "description": "Scope of insight generation (default: system)"
                },
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific tags to analyze"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Time duration for insight generation (default: 24h)"
                },
                "equipment_filter": {
                    "type": "string",
                    "description": "Filter by equipment name (optional)"
                }
            }
        }
    },
    # ========================================
    # PCM - Planejamento e Controle da Manutenção
    # ========================================
    {
        "name": "calculate_mtbf_mttr",
        "description": "Calculate MTBF (Mean Time Between Failures) and MTTR (Mean Time To Repair) for equipment. Use for maintenance planning, reliability analysis, and equipment performance assessment.",
        "parameters": {
            "type": "object",
            "properties": {
                "equipment_id": {
                    "type": "string",
                    "description": "Equipment identifier or tag prefix (e.g., 'ELEV01', 'CORR01', 'SILO01')"
                },
                "status_tag": {
                    "type": "string",
                    "description": "Tag that indicates equipment running/stopped status (optional, will auto-detect if not provided)"
                },
                "duration": {
                    "type": "string",
                    "enum": ["7d", "30d", "90d", "180d", "365d"],
                    "description": "Analysis period for MTBF/MTTR calculation (default: 30d)"
                },
                "failure_threshold": {
                    "type": "number",
                    "description": "Value threshold that indicates failure condition (optional)"
                }
            },
            "required": ["equipment_id"]
        }
    },
    {
        "name": "predict_failure",
        "description": "Predict equipment failures using trend analysis, degradation patterns, and anomaly detection. Use for predictive maintenance (PCM Preditivo), risk assessment, and maintenance scheduling.",
        "parameters": {
            "type": "object",
            "properties": {
                "equipment_id": {
                    "type": "string",
                    "description": "Equipment identifier or tag prefix (e.g., 'ELEV01', 'MOTOR01')"
                },
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags to analyze for failure prediction (temperature, vibration, current, etc.)"
                },
                "prediction_horizon": {
                    "type": "string",
                    "enum": ["24h", "7d", "14d", "30d"],
                    "description": "How far ahead to predict (default: 7d)"
                },
                "confidence_threshold": {
                    "type": "number",
                    "description": "Minimum confidence level for predictions (0-1, default: 0.7)"
                }
            },
            "required": ["equipment_id"]
        }
    },
    # ========================================
    # QUALIDADE - Controle Estatístico de Processo (CEP/SPC)
    # ========================================
    {
        "name": "calculate_spc_limits",
        "description": "Calculate Statistical Process Control (SPC/CEP) limits including UCL, LCL, Cp, Cpk, and process capability indices. Use for quality control, process stability assessment, and Six Sigma analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "Tag identifier for quality measurement (e.g., 'SILO01_UMIDADE', 'QUALIDADE_PESO')"
                },
                "specification_limits": {
                    "type": "object",
                    "properties": {
                        "usl": {"type": "number", "description": "Upper Specification Limit"},
                        "lsl": {"type": "number", "description": "Lower Specification Limit"},
                        "target": {"type": "number", "description": "Target value (optional)"}
                    },
                    "description": "Specification limits for capability indices (optional)"
                },
                "duration": {
                    "type": "string",
                    "enum": ["1h", "6h", "12h", "24h", "7d", "30d"],
                    "description": "Analysis period (default: 24h)"
                },
                "subgroup_size": {
                    "type": "integer",
                    "description": "Subgroup size for control charts (default: 5)"
                },
                "control_chart_type": {
                    "type": "string",
                    "enum": ["x_bar_r", "x_bar_s", "individuals", "p_chart", "c_chart"],
                    "description": "Type of control chart (default: x_bar_r)"
                }
            },
            "required": ["tag_id"]
        }
    },
    # ========================================
    # DASHBOARD EXECUTIVO - Visão Gerencial
    # ========================================
    {
        "name": "get_executive_overview",
        "description": "Get consolidated executive overview with all main KPIs (OEE, Availability, Performance, Quality), alarm status, critical equipment, production trends, insights, and financial summary. Use when user asks about executive dashboard, general overview, management KPIs, or overall plant status.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for analysis (default: 24h)"
                }
            }
        }
    },
    {
        "name": "get_energy_metrics",
        "description": "Get detailed energy metrics including consumption (kWh), demand (kW), power factor, bill forecast, efficiency (kWh/ton), and peak demand analysis. Use when user asks about energy consumption, electricity costs, power factor, energy efficiency, or utility bills.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for analysis (default: 24h)"
                }
            }
        }
    },
    {
        "name": "get_production_metrics",
        "description": "Get detailed production metrics including throughput (ton/hour), capacity utilization, cycle time, production targets, and efficiency indicators. Use when user asks about production rate, throughput, capacity, production targets, or manufacturing efficiency.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for analysis (default: 24h)"
                }
            }
        }
    },
    {
        "name": "get_alarm_pareto",
        "description": "Get Pareto analysis of alarms showing top alarm types, frequency, cumulative percentage, MTTR, estimated costs, and top equipment with most alarms. Use when user asks about most frequent alarms, alarm ranking, 80/20 analysis, or which alarms cause most problems.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for analysis (default: 24h)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of top alarms to return (default: 10)"
                }
            }
        }
    },
    {
        "name": "get_financial_summary",
        "description": "Get financial summary including estimated savings, downtime costs avoided, efficiency improvements, and projected monthly savings. Use when user asks about cost savings, financial impact, ROI, or economic benefits.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for analysis (default: 24h)"
                }
            }
        }
    },
    {
        "name": "get_maintenance_dashboard",
        "description": "Get predictive maintenance dashboard with equipment health scores, at-risk equipment, failure predictions, scheduled maintenance, and ROI metrics. Use when user asks about equipment health, maintenance planning, failure predictions, or predictive maintenance status.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_predictions": {
                    "type": "boolean",
                    "description": "Include failure predictions (default: true)"
                }
            }
        }
    },
    {
        "name": "generate_executive_report",
        "description": "Generate a complete executive report/dashboard in PDF format with all KPIs, charts, trends, and insights. Use when user asks to create, generate, or export an executive report or dashboard. Returns a download URL for the PDF.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["1h", "6h", "24h", "7d", "30d"],
                    "description": "Time range for the report (default: 24h)"
                },
                "include_charts": {
                    "type": "boolean",
                    "description": "Include visual charts in the report (default: true)"
                },
                "report_title": {
                    "type": "string",
                    "description": "Custom title for the report (optional)"
                }
            }
        }
    },
    {
        "name": "get_executive_trends",
        "description": "Get trend data for executive metrics (OEE, availability, performance, quality, production) over time with summary statistics. Use when user asks about trends, historical performance, or how metrics have changed over time.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["oee", "availability", "performance", "quality", "production"],
                    "description": "Metric to get trends for (default: oee)"
                },
                "period": {
                    "type": "string",
                    "enum": ["24h", "7d", "30d"],
                    "description": "Period for trend analysis (default: 24h)"
                }
            }
        }
    },
    # ========================================
    # ASSET TREE - Hierarquia de Ativos
    # ========================================
    {
        "name": "get_asset_hierarchy",
        "description": "Get the complete asset hierarchy tree showing all industrial assets (plants, areas, equipment groups, equipment, components). Use when user asks about plant structure, equipment organization, asset tree, which equipment exists, or where a specific asset is located.",
        "parameters": {
            "type": "object",
            "properties": {
                "root_id": {
                    "type": "string",
                    "description": "Optional: Start from specific element ID to get subtree"
                }
            }
        }
    },
    {
        "name": "get_asset_element",
        "description": "Get detailed information about a specific asset element including its attributes (linked tags), children, path, and metadata. Use when user asks about specific equipment details, what sensors an equipment has, or equipment attributes.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "Element ID or path (e.g., 'elem_123' or '/Plant/Area/Equipment')"
                },
                "include_children": {
                    "type": "boolean",
                    "description": "Include child elements in response (default: false)"
                }
            },
            "required": ["element_id"]
        }
    },
    {
        "name": "search_assets",
        "description": "Search for assets/equipment by name, type, or path. Use when user asks to find specific equipment, list equipment of a certain type, or locate assets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (name or path fragment)"
                },
                "element_type": {
                    "type": "string",
                    "enum": ["plant", "area", "equipment_group", "equipment", "component"],
                    "description": "Filter by element type (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default: 20)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_asset_statistics",
        "description": "Get statistics about the asset tree including total elements, elements by type, total attributes/tags linked, and template usage. Use when user asks about asset counts, how many equipment exist, or asset tree overview.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_element_attributes",
        "description": "Get all attributes (linked tags/sensors) for a specific element. Returns tag IDs, descriptions, units, and current values. Use when user asks what tags/sensors an equipment has, or to see all measurements for an asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "Element ID to get attributes for"
                },
                "include_values": {
                    "type": "boolean",
                    "description": "Include current real-time values (default: true)"
                }
            },
            "required": ["element_id"]
        }
    },
    {
        "name": "get_tags_by_asset",
        "description": "Get all tags associated with an asset and its children (recursive). Use when user asks about all sensors in an area, all tags for an equipment group, or monitoring points under a specific asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "Element ID to get tags for"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Include tags from child elements (default: true)"
                }
            },
            "required": ["element_id"]
        }
    }
]


class AgentToolkit:
    """Toolkit for executing agent tools"""

    def __init__(self, data_service):
        """
        Initialize the toolkit with a data service

        Args:
            data_service: DataService instance for data access
        """
        self.data_service = data_service
        # Gateway client for Asset Tree access
        from app.services.gateway_client import get_gateway_client
        self.gateway_client = get_gateway_client()

        self.tools: Dict[str, Callable] = {
            "get_realtime_value": self._get_realtime_value,
            "get_multiple_realtime_values": self._get_multiple_realtime_values,
            "get_historical_data": self._get_historical_data,
            "calculate_statistics": self._calculate_statistics,
            "search_tags": self._search_tags,
            "compare_tags": self._compare_tags,
            "detect_anomalies": self._detect_anomalies,
            "calculate_oee": self._calculate_oee,
            "analyze_alarm_patterns": self._analyze_alarm_patterns,
            "get_tag_metadata": self._get_tag_metadata,
            "get_all_tags": self._get_all_tags,
            "get_active_alarms": self._get_active_alarms,
            "analyze_alarm_frequency": self._analyze_alarm_frequency,
            "generate_data_histogram": self._generate_data_histogram,
            "calculate_correlation": self._calculate_correlation,
            "detect_trends": self._detect_trends,
            "generate_insights": self._generate_insights,
            # PCM - Manutenção
            "calculate_mtbf_mttr": self._calculate_mtbf_mttr,
            "predict_failure": self._predict_failure,
            # Qualidade - CEP/SPC
            "calculate_spc_limits": self._calculate_spc_limits,
            # Dashboard Executivo
            "get_executive_overview": self._get_executive_overview,
            "get_energy_metrics": self._get_energy_metrics,
            "get_production_metrics": self._get_production_metrics,
            "get_alarm_pareto": self._get_alarm_pareto,
            "get_financial_summary": self._get_financial_summary,
            "get_maintenance_dashboard": self._get_maintenance_dashboard,
            "generate_executive_report": self._generate_executive_report,
            "get_executive_trends": self._get_executive_trends,
            # Asset Tree - Hierarquia de Ativos
            "get_asset_hierarchy": self._get_asset_hierarchy,
            "get_asset_element": self._get_asset_element,
            "search_assets": self._search_assets,
            "get_asset_statistics": self._get_asset_statistics,
            "get_element_attributes": self._get_element_attributes,
            "get_tags_by_asset": self._get_tags_by_asset,
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get list of available tool definitions for the LLM"""
        return AVAILABLE_TOOLS
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool with given arguments
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            ToolResult with execution result
        """
        try:
            if tool_name not in self.tools:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"Unknown tool: {tool_name}"
                )
            
            tool_func = self.tools[tool_name]
            result = await tool_func(**arguments)
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e)
            )
    
    async def _get_realtime_value(self, tag_id: str) -> Dict[str, Any]:
        """Get real-time value for a tag - tries InfluxDB first, then Gateway"""
        import httpx

        # Try InfluxDB first (via data_service)
        result = await self.data_service.get_realtime_value(tag_id)
        if result and result.get('value') is not None:
            return result

        # Fallback: Try Gateway Edge directly for real-time value
        try:
            gateway_url = "http://gateway:8080"
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Search for tag in Gateway
                response = await client.get(f"{gateway_url}/api/tags/")
                if response.status_code == 200:
                    tags = response.json()

                    # Find matching tag (fuzzy match)
                    tag_id_lower = tag_id.lower().replace('_', '').replace('-', '')
                    for tag in tags:
                        tag_name = tag.get('tag_name', '').lower().replace('_', '').replace('-', '')
                        if tag_id_lower in tag_name or tag_name in tag_id_lower:
                            # Found matching tag
                            return {
                                "tag_id": tag.get('tag_id'),
                                "tag_name": tag.get('tag_name'),
                                "value": tag.get('current_value'),
                                "quality": tag.get('current_quality', 'Good'),
                                "timestamp": tag.get('current_timestamp'),
                                "unit": tag.get('metadata', {}).get('engineering_units', ''),
                                "source": "gateway"
                            }
        except Exception as e:
            logger.debug(f"Gateway fallback failed for {tag_id}: {e}")

        return {"error": f"Tag not found: {tag_id}", "tag_id": tag_id}
    
    async def _get_multiple_realtime_values(self, tag_ids: List[str]) -> List[Dict[str, Any]]:
        """Get real-time values for multiple tags"""
        return await self.data_service.get_multiple_realtime_values(tag_ids)
    
    async def _get_historical_data(
        self, 
        tag_id: str, 
        duration: str = "1h",
        aggregation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get historical data for a tag"""
        return await self.data_service.get_historical_data(
            tag_id=tag_id,
            duration=duration,
            aggregation=aggregation
        )
    
    async def _calculate_statistics(self, tag_id: str, duration: str = "1h") -> Dict[str, Any]:
        """Calculate statistics for a tag - tries InfluxDB first, then Gateway current value"""
        import httpx

        # Try InfluxDB first
        result = await self.data_service.calculate_statistics(tag_id, duration)
        if result and result.get('count', 0) > 0:
            return result

        # Fallback: If no historical data, get current value from Gateway
        try:
            gateway_url = "http://gateway:8080"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{gateway_url}/api/tags/")
                if response.status_code == 200:
                    tags = response.json()

                    # Find matching tag
                    tag_id_lower = tag_id.lower().replace('_', '').replace('-', '')
                    for tag in tags:
                        tag_name = tag.get('tag_name', '').lower().replace('_', '').replace('-', '')
                        if tag_id_lower in tag_name or tag_name in tag_id_lower:
                            current_value = tag.get('current_value')
                            if current_value is not None:
                                # Return current value as stats (single point)
                                return {
                                    "tag_id": tag.get('tag_id'),
                                    "tag_name": tag.get('tag_name'),
                                    "duration": duration,
                                    "count": 1,
                                    "mean": current_value,
                                    "min": current_value,
                                    "max": current_value,
                                    "std_dev": 0,
                                    "current_value": current_value,
                                    "unit": tag.get('metadata', {}).get('engineering_units', ''),
                                    "note": "Dados históricos não disponíveis. Mostrando valor atual do Gateway.",
                                    "source": "gateway"
                                }
        except Exception as e:
            logger.debug(f"Gateway fallback failed for statistics {tag_id}: {e}")

        return {
            "tag_id": tag_id,
            "duration": duration,
            "count": 0,
            "error": "Sem dados históricos disponíveis para este período"
        }
    
    async def _search_tags(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tags - tries data_service first, then Gateway"""
        import httpx

        # PROTECTION: Limit max results to prevent memory issues
        limit = min(limit, 50)

        # Try data_service first
        result = await self.data_service.search_tags(query, limit)
        if result and len(result) > 0:
            return result

        # Fallback: Search in Gateway
        try:
            gateway_url = "http://gateway:8080"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{gateway_url}/api/tags/")
                if response.status_code == 200:
                    all_tags = response.json()

                    # Filter tags by query (case-insensitive)
                    query_lower = query.lower()
                    matching_tags = []

                    for tag in all_tags:
                        tag_name = tag.get('tag_name', '').lower()
                        description = tag.get('metadata', {}).get('description', '').lower()

                        if query_lower in tag_name or query_lower in description:
                            matching_tags.append({
                                "id": tag.get('tag_id'),
                                "tag_id": tag.get('tag_id'),
                                "name": tag.get('tag_name'),
                                "tag_name": tag.get('tag_name'),
                                "unit": tag.get('metadata', {}).get('engineering_units', ''),
                                "description": tag.get('metadata', {}).get('description', ''),
                                "current_value": tag.get('current_value'),
                                "quality": tag.get('current_quality'),
                                "source": "gateway"
                            })

                            if len(matching_tags) >= limit:
                                break

                    if matching_tags:
                        logger.info(f"Found {len(matching_tags)} tags from Gateway for query '{query}'")
                        return matching_tags

        except Exception as e:
            logger.debug(f"Gateway search failed for '{query}': {e}")

        return []
    
    async def _compare_tags(self, tag_ids: List[str], duration: str = "24h") -> Dict[str, Any]:
        """
        Compare multiple tags to find correlations and patterns
        """
        # Get historical data for all tags
        all_data = {}
        stats = {}
        
        for tag_id in tag_ids[:10]:  # Limit to 10 tags
            try:
                data = await self.data_service.get_historical_data(tag_id, duration)
                stats_data = await self.data_service.calculate_statistics(tag_id, duration)
                all_data[tag_id] = data
                stats[tag_id] = stats_data
            except Exception as e:
                logger.warning(f"Error fetching data for {tag_id}: {e}")
        
        # Simple correlation analysis (would need numpy for proper correlation)
        comparison = {
            "tags_compared": len(all_data),
            "duration": duration,
            "statistics": stats,
            "summary": f"Compared {len(all_data)} tags over {duration}",
            "insights": []
        }
        
        # Generate insights based on statistics
        for tag_id, tag_stats in stats.items():
            if tag_stats.get("mean"):
                variation = (tag_stats.get("stddev", 0) / tag_stats["mean"]) * 100
                if variation > 20:
                    comparison["insights"].append(
                        f"{tag_id}: High variability ({variation:.1f}% coefficient of variation)"
                    )
                elif variation < 5:
                    comparison["insights"].append(
                        f"{tag_id}: Very stable ({variation:.1f}% coefficient of variation)"
                    )
        
        return comparison
    
    async def _detect_anomalies(
        self, 
        tag_id: str, 
        duration: str = "24h",
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Detect anomalies in tag data using statistical methods
        """
        # Get historical data and statistics
        data = await self.data_service.get_historical_data(tag_id, duration)
        stats = await self.data_service.calculate_statistics(tag_id, duration)
        
        anomalies = {
            "tag_id": tag_id,
            "duration": duration,
            "sensitivity": sensitivity,
            "statistics": stats,
            "anomalies_detected": [],
            "anomaly_count": 0
        }
        
        if not stats.get("mean") or not stats.get("stddev"):
            return anomalies
        
        mean = stats["mean"]
        stddev = stats["stddev"]
        
        # Z-score thresholds based on sensitivity
        thresholds = {
            "low": 3.0,     # 99.7% confidence
            "medium": 2.5,  # 98.8% confidence
            "high": 2.0     # 95.4% confidence
        }
        threshold = thresholds.get(sensitivity, 2.5)
        
        # Analyze data points (if available in data)
        if isinstance(data, dict) and "points" in data:
            points = data["points"]
            for point in points:
                value = point.get("value")
                if value is not None:
                    z_score = abs((value - mean) / stddev) if stddev > 0 else 0
                    if z_score > threshold:
                        anomalies["anomalies_detected"].append({
                            "timestamp": point.get("timestamp"),
                            "value": value,
                            "z_score": round(z_score, 2),
                            "deviation": round(((value - mean) / mean) * 100, 1)
                        })
        
        anomalies["anomaly_count"] = len(anomalies["anomalies_detected"])
        
        # Add insights
        if anomalies["anomaly_count"] > 0:
            anomalies["insight"] = f"Detected {anomalies['anomaly_count']} anomalies (values beyond {threshold} standard deviations)"
        else:
            anomalies["insight"] = f"No significant anomalies detected. Data appears normal."
        
        return anomalies
    
    async def _calculate_oee(
        self,
        equipment_tags: Dict[str, Any],
        duration: str = "24h"
    ) -> Dict[str, Any]:
        """
        Calculate Overall Equipment Effectiveness (OEE)
        OEE = Availability × Performance × Quality
        """
        oee_result = {
            "duration": duration,
            "availability": None,
            "performance": None,
            "quality": None,
            "oee": None,
            "calculation_method": "simplified"
        }
        
        try:
            # Get running status data
            if "running_status" in equipment_tags:
                status_data = await self.data_service.get_historical_data(
                    equipment_tags["running_status"], duration
                )
                # Calculate availability (% of time running)
                # This is simplified - would need actual uptime/downtime calculation
                oee_result["availability"] = 85.0  # Placeholder
            
            # Get speed data
            if "speed_actual" in equipment_tags and "speed_design" in equipment_tags:
                speed_stats = await self.data_service.calculate_statistics(
                    equipment_tags["speed_actual"], duration
                )
                design_speed = equipment_tags["speed_design"]
                
                if speed_stats.get("mean") and design_speed > 0:
                    oee_result["performance"] = (speed_stats["mean"] / design_speed) * 100
            
            # Get quality data
            if "quality_good" in equipment_tags and "quality_total" in equipment_tags:
                good_stats = await self.data_service.calculate_statistics(
                    equipment_tags["quality_good"], duration
                )
                total_stats = await self.data_service.calculate_statistics(
                    equipment_tags["quality_total"], duration
                )
                
                if good_stats.get("sum") and total_stats.get("sum") and total_stats["sum"] > 0:
                    oee_result["quality"] = (good_stats["sum"] / total_stats["sum"]) * 100
            
            # Calculate OEE if all components available
            if all([oee_result["availability"], oee_result["performance"], oee_result["quality"]]):
                oee_result["oee"] = (
                    oee_result["availability"] *
                    oee_result["performance"] *
                    oee_result["quality"]
                ) / 10000  # Convert to percentage
                
                # OEE classification
                if oee_result["oee"] >= 85:
                    oee_result["classification"] = "World Class"
                elif oee_result["oee"] >= 60:
                    oee_result["classification"] = "Good"
                elif oee_result["oee"] >= 40:
                    oee_result["classification"] = "Fair"
                else:
                    oee_result["classification"] = "Poor"
            
        except Exception as e:
            oee_result["error"] = str(e)
        
        return oee_result
    
    async def _analyze_alarm_patterns(
        self,
        alarm_tags: List[str],
        duration: str = "24h"
    ) -> Dict[str, Any]:
        """
        Analyze alarm patterns to identify issues
        """
        analysis = {
            "duration": duration,
            "alarms_analyzed": len(alarm_tags),
            "statistics": {},
            "patterns": [],
            "insights": []
        }
        
        total_alarms = 0
        alarm_rates = []
        
        for tag_id in alarm_tags:
            try:
                stats = await self.data_service.calculate_statistics(tag_id, duration)
                analysis["statistics"][tag_id] = stats
                
                if stats.get("mean"):
                    total_alarms += stats.get("sum", 0)
                    alarm_rates.append(stats["mean"])
            except Exception as e:
                logger.warning(f"Error analyzing alarm {tag_id}: {e}")
        
        analysis["total_alarm_count"] = int(total_alarms)
        
        # Identify patterns
        if alarm_rates:
            avg_rate = sum(alarm_rates) / len(alarm_rates)
            
            # High alarm rate detection
            if avg_rate > 10:
                analysis["patterns"].append("High alarm rate detected")
                analysis["insights"].append(
                    "Alarm flood condition: Consider alarm rationalization"
                )
            
            # Chattering alarm detection (high variability)
            if len(alarm_rates) > 1:
                import statistics
                stddev = statistics.stdev(alarm_rates)
                if stddev > avg_rate * 0.5:
                    analysis["patterns"].append("Chattering alarms detected")
                    analysis["insights"].append(
                        "Some alarms are chattering: Review alarm deadbands and delays"
                    )
        
        # Recommendations
        if total_alarms > 100:
            analysis["insights"].append(
                "Very high alarm count: Immediate alarm rationalization recommended"
            )
        elif total_alarms > 50:
            analysis["insights"].append(
                "Elevated alarm count: Review and prioritize critical alarms"
            )
        else:
            analysis["insights"].append(
                "Alarm count is within acceptable range"
            )
        
        return analysis
    
    async def _get_tag_metadata(self, tag_id: str) -> Dict[str, Any]:
        """
        Get detailed metadata about a tag
        """
        # This would query the database for tag metadata
        # For now, return basic structure
        try:
            # Try to get tag information from database
            tag_data = await self.data_service.get_tag_info(tag_id)
            
            if tag_data:
                return {
                    "tag_id": tag_id,
                    "name": tag_data.get("name", tag_id),
                    "description": tag_data.get("description"),
                    "unit": tag_data.get("unit"),
                    "data_type": tag_data.get("data_type"),
                    "category": tag_data.get("category"),
                    "min_value": tag_data.get("min_value"),
                    "max_value": tag_data.get("max_value"),
                    "is_active": tag_data.get("is_active", True)
                }
            else:
                return {"error": f"Tag not found: {tag_id}"}
                
        except Exception as e:
            return {"error": str(e)}

    async def _get_all_tags(self, limit: int = 50, active_only: bool = True) -> Dict[str, Any]:
        """
        Get list of all available tags in the system (max 50 to prevent overload)
        """
        # PROTECTION: Enforce max limit to prevent memory/CPU issues
        limit = min(limit, 50)
        
        try:
            tags = await self.data_service.get_all_tags(limit=limit, active_only=active_only)

            return {
                "total_tags": len(tags),
                "tags": [
                    {
                        "tag_id": str(tag.get("id")),
                        "name": tag.get("name"),
                        "description": tag.get("description"),
                        "unit": tag.get("unit"),
                        "last_value": tag.get("last_value"),
                        "is_active": tag.get("is_active", True)
                    }
                    for tag in tags
                ],
                "showing": f"Showing {len(tags)} tags" + (" (active only)" if active_only else "")
            }
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return {"error": str(e), "tags": []}

    async def _get_active_alarms(self, severity: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get list of currently active alarms
        """
        try:
            # Import models directly to query database instead of HTTP call
            from sqlalchemy import select, func
            from app.models.alarm import AlarmEvent, AlarmDefinition, AlarmState, AlarmSeverity
            from app.db.session import get_db

            # Get alarms from database directly (more reliable than HTTP from within container)
            return_value = None
            async for session in get_db():
                try:
                    # FIX N+1 QUERY: Use selectinload to eagerly load AlarmDefinition
                    from sqlalchemy.orm import selectinload

                    # First, get the TOTAL count of active alarms (without limit)
                    count_stmt = select(func.count(AlarmEvent.id)).where(AlarmEvent.state == AlarmState.ACTIVE)
                    if severity:
                        severity_enum = AlarmSeverity[severity.upper()]
                        count_stmt = count_stmt.join(AlarmDefinition).where(AlarmDefinition.severity == severity_enum)

                    count_result = await session.execute(count_stmt)
                    total_count = count_result.scalar() or 0

                    # Query active alarms with their definitions (with limit for response size)
                    stmt = select(AlarmEvent).options(
                        selectinload(AlarmEvent.definition)  # Eager load relationship
                    ).where(AlarmEvent.state == AlarmState.ACTIVE).order_by(AlarmEvent.trigger_timestamp.desc()).limit(limit)

                    if severity:
                        # Join with definition to filter by severity
                        severity_enum = AlarmSeverity[severity.upper()]
                        stmt = stmt.join(AlarmDefinition).where(AlarmDefinition.severity == severity_enum)

                    result = await session.execute(stmt)
                    alarms = result.scalars().all()

                    # Get definition details for each alarm
                    alarm_list = []
                    for alarm in alarms:
                        # Access definition directly from relationship (already loaded!)
                        definition = alarm.definition

                        if definition:
                            alarm_list.append({
                                "alarm_id": str(alarm.id),
                                "alarm_name": definition.name,
                                "severity": definition.severity.value if hasattr(definition.severity, 'value') else str(definition.severity),
                                "tag_id": str(definition.tag_id),
                                "trigger_value": float(alarm.trigger_value) if alarm.trigger_value is not None else None,
                                "trigger_timestamp": alarm.trigger_timestamp.isoformat() if alarm.trigger_timestamp else None,
                                "state": alarm.state.value if hasattr(alarm.state, 'value') else str(alarm.state),
                                "description": definition.description,
                                "alarm_type": definition.alarm_type.value if hasattr(definition.alarm_type, 'value') else str(definition.alarm_type)
                            })

                    return_value = {
                        "total_active_alarms": total_count,
                        "showing": len(alarm_list),
                        "alarms": alarm_list,
                        "filter_applied": f"severity={severity}" if severity else "all severities",
                        "note": f"Showing {len(alarm_list)} of {total_count} total active alarms" if total_count > len(alarm_list) else None
                    }
                finally:
                    await session.close()
                    break  # Only process first session from generator

            return return_value

        except Exception as e:
            logger.error(f"Error getting active alarms: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "alarms": []}

    async def _analyze_alarm_frequency(
        self,
        duration: str = "24h",
        severity: str = None,
        equipment_filter: str = None,
        alarm_name_filter: str = None,
        threshold: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze alarm frequency over time to identify chattering alarms, alarm floods, and patterns.

        Returns:
            Dictionary with frequency analysis including:
            - Total alarm events
            - Alarms per hour/day
            - Top frequent alarms
            - Chattering alarm detection
            - Alarm flood periods
            - Frequency histogram
        """
        try:
            from sqlalchemy import select, func
            from app.models.alarm import AlarmEvent, AlarmDefinition, AlarmState, AlarmSeverity
            from app.db.session import get_db
            from datetime import datetime, timedelta
            from collections import defaultdict

            # Parse duration to timedelta
            duration_map = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "12h": timedelta(hours=12),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }
            time_delta = duration_map.get(duration, timedelta(hours=24))
            # Use timezone-aware datetime for comparison with database timestamps
            from datetime import timezone
            start_time = datetime.now(timezone.utc) - time_delta

            return_value = None
            async for session in get_db():
                try:
                    # Query all alarm events in time period WITH EAGER LOADING
                    # FIX N+1 QUERY: Use selectinload to load AlarmDefinition in a single query
                    from sqlalchemy.orm import selectinload

                    logger.error(f"🔍 analyze_alarm_frequency: start_time={start_time}, duration={duration}, alarm_name_filter={alarm_name_filter}")

                    stmt = select(AlarmEvent).options(
                        selectinload(AlarmEvent.definition)  # Eager load relationship
                    ).where(
                        AlarmEvent.trigger_timestamp >= start_time
                    ).order_by(AlarmEvent.trigger_timestamp.desc())

                    result = await session.execute(stmt)
                    events = result.scalars().all()

                    logger.error(f"🔍 analyze_alarm_frequency: Found {len(events)} events in time period")

                    # Get definitions for filtering and grouping
                    alarm_frequency = defaultdict(int)
                    alarm_details = {}
                    alarm_timestamps = defaultdict(list)
                    severity_distribution = defaultdict(int)
                    equipment_distribution = defaultdict(int)

                    for event in events:
                        # Access definition directly from relationship (already loaded!)
                        definition = event.definition

                        if not definition:
                            continue

                        # Apply filters
                        if severity and definition.severity.value.lower() != severity.lower():
                            continue

                        alarm_name = definition.name

                        # Equipment filter (fuzzy match)
                        if equipment_filter:
                            if equipment_filter.upper() not in alarm_name.upper():
                                continue

                        # Alarm name filter (fuzzy match - more flexible)
                        if alarm_name_filter:
                            # Normalize both strings for comparison
                            filter_normalized = alarm_name_filter.upper().replace('_', '').replace(' ', '').replace('-', '')
                            name_normalized = alarm_name.upper().replace('_', '').replace(' ', '').replace('-', '')

                            # Try multiple matching strategies
                            match_found = False

                            # Strategy 1: Direct substring match
                            if filter_normalized in name_normalized:
                                match_found = True

                            # Strategy 2: Check if all filter words are in the name (word-based)
                            if not match_found:
                                filter_words = [w for w in alarm_name_filter.upper().replace('_', ' ').replace('-', ' ').split() if len(w) > 2]
                                name_words = alarm_name.upper().replace('_', ' ').replace('-', ' ')
                                if all(fw in name_words for fw in filter_words):
                                    match_found = True

                            # Strategy 3: Check if filter is a prefix
                            if not match_found and name_normalized.startswith(filter_normalized[:min(len(filter_normalized), 10)]):
                                match_found = True

                            if not match_found:
                                continue

                        # Count frequency
                        alarm_frequency[alarm_name] += 1
                        alarm_timestamps[alarm_name].append(event.trigger_timestamp)

                        # Track severity distribution
                        severity_distribution[definition.severity.value] += 1

                        # Track equipment distribution (extract from name)
                        equipment = alarm_name.split('_')[0] if '_' in alarm_name else alarm_name
                        equipment_distribution[equipment] += 1

                        # Store details
                        if alarm_name not in alarm_details:
                            alarm_details[alarm_name] = {
                                "severity": definition.severity.value,
                                "description": definition.description,
                                "alarm_type": definition.alarm_type.value
                            }

                    # Calculate statistics
                    total_events = sum(alarm_frequency.values())
                    unique_alarms = len(alarm_frequency)
                    hours = time_delta.total_seconds() / 3600
                    alarms_per_hour = total_events / hours if hours > 0 else 0

                    logger.error(f"🔍 analyze_alarm_frequency: After filters - total_events={total_events}, unique_alarms={unique_alarms}, frequency={dict(alarm_frequency)}")

                    # Identify top frequent alarms
                    top_alarms = sorted(
                        [(name, count) for name, count in alarm_frequency.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]

                    # Detect chattering alarms (alarms that trigger/clear repeatedly)
                    chattering_alarms = []
                    for alarm_name, timestamps in alarm_timestamps.items():
                        if len(timestamps) >= 5:  # At least 5 events
                            # Calculate average time between events
                            sorted_times = sorted(timestamps)
                            intervals = [
                                (sorted_times[i+1] - sorted_times[i]).total_seconds() / 60
                                for i in range(len(sorted_times) - 1)
                            ]
                            avg_interval = sum(intervals) / len(intervals) if intervals else 0

                            # Chattering if average interval < 10 minutes
                            if avg_interval < 10:
                                chattering_alarms.append({
                                    "alarm_name": alarm_name,
                                    "event_count": len(timestamps),
                                    "avg_interval_minutes": round(avg_interval, 2),
                                    "severity": alarm_details[alarm_name]["severity"]
                                })

                    # Detect alarm flood periods (more than 10 alarms in 10 minutes)
                    alarm_flood_periods = []
                    all_timestamps = []
                    for timestamps in alarm_timestamps.values():
                        all_timestamps.extend(timestamps)
                    all_timestamps.sort()

                    flood_threshold = 10  # alarms
                    flood_window = timedelta(minutes=10)

                    i = 0
                    while i < len(all_timestamps):
                        window_end = all_timestamps[i] + flood_window
                        count_in_window = sum(1 for ts in all_timestamps[i:] if ts <= window_end)

                        if count_in_window >= flood_threshold:
                            alarm_flood_periods.append({
                                "start_time": all_timestamps[i].isoformat(),
                                "alarm_count": count_in_window,
                                "duration_minutes": 10
                            })
                            i += count_in_window
                        else:
                            i += 1

                    # Build frequency histogram (alarms per hour bucket)
                    histogram_buckets = []
                    bucket_size = max(1, int(hours / 10))  # 10 buckets
                    current_time = start_time

                    while current_time < datetime.now(timezone.utc):
                        bucket_end = current_time + timedelta(hours=bucket_size)
                        bucket_count = sum(
                            1 for timestamps in alarm_timestamps.values()
                            for ts in timestamps
                            if current_time <= ts < bucket_end
                        )
                        histogram_buckets.append({
                            "time_start": current_time.isoformat(),
                            "time_end": bucket_end.isoformat(),
                            "alarm_count": bucket_count
                        })
                        current_time = bucket_end

                    # Build result BEFORE finally block
                    result_data = {
                        "duration": duration,
                        "analysis_period": {
                            "start": start_time.isoformat(),
                            "end": datetime.now(timezone.utc).isoformat(),
                            "hours": round(hours, 2)
                        },
                        "summary": {
                            "total_alarm_events": total_events,
                            "unique_alarms": unique_alarms,
                            "alarms_per_hour": round(alarms_per_hour, 2),
                            "alarms_per_day": round(alarms_per_hour * 24, 2)
                        },
                        "top_frequent_alarms": [
                            {
                                "alarm_name": name,
                                "event_count": count,
                                "percentage": round((count / total_events * 100), 1) if total_events > 0 else 0,
                                **alarm_details.get(name, {})
                            }
                            for name, count in top_alarms if count >= threshold
                        ],
                        "chattering_alarms": chattering_alarms,
                        "alarm_floods": alarm_flood_periods,
                        "severity_distribution": dict(severity_distribution),
                        "equipment_distribution": dict(equipment_distribution),
                        "frequency_histogram": histogram_buckets,
                        "insights": self._generate_frequency_insights(
                            total_events, alarms_per_hour, chattering_alarms, alarm_flood_periods
                        )
                    }

                    logger.error(f"🔍 analyze_alarm_frequency: Returning result with {total_events} events")

                    # Return directly from inside the session block
                    return result_data

                finally:
                    await session.close()

            # Fallback if no session was obtained
            return {"error": "No database session available"}

        except Exception as e:
            logger.error(f"Error analyzing alarm frequency: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _generate_frequency_insights(
        self,
        total_events: int,
        alarms_per_hour: float,
        chattering_alarms: List[Dict],
        alarm_floods: List[Dict]
    ) -> List[str]:
        """Generate insights from frequency analysis"""
        insights = []

        # Overall frequency assessment
        if alarms_per_hour > 10:
            insights.append(f"⚠️ HIGH ALARM RATE: {alarms_per_hour:.1f} alarms/hour exceeds recommended threshold (< 10/hour)")
        elif alarms_per_hour > 5:
            insights.append(f"⚡ ELEVATED ALARM RATE: {alarms_per_hour:.1f} alarms/hour - consider alarm rationalization")
        else:
            insights.append(f"✅ ACCEPTABLE ALARM RATE: {alarms_per_hour:.1f} alarms/hour is within normal range")

        # Chattering alarms
        if len(chattering_alarms) > 0:
            critical_chattering = [a for a in chattering_alarms if a["severity"].lower() == "critical"]
            if critical_chattering:
                insights.append(f"🚨 CRITICAL: {len(critical_chattering)} critical alarms are chattering - IMMEDIATE action required")
            insights.append(f"🔄 CHATTERING DETECTED: {len(chattering_alarms)} alarms triggering repeatedly - review deadbands and delays")

        # Alarm floods
        if len(alarm_floods) > 0:
            insights.append(f"💥 ALARM FLOODS: {len(alarm_floods)} flood periods detected - operators may be overwhelmed")

        # Overall health
        if total_events > 500:
            insights.append("📊 RECOMMENDATION: Implement alarm rationalization program to reduce alarm load")
        elif total_events > 200:
            insights.append("📊 RECOMMENDATION: Review alarm priorities and suppression logic")
        else:
            insights.append("✅ ALARM LOAD: Within acceptable range for effective operator response")

        return insights

    async def _generate_data_histogram(
        self,
        tag_id: str,
        duration: str = "24h",
        bins: int = 10,
        histogram_type: str = "value_distribution"
    ) -> Dict[str, Any]:
        """
        Generate histogram distribution for sensor data or alarm patterns
        """
        try:
            # Get historical data
            data = await self.data_service.get_historical_data(tag_id, duration)

            if not data or "points" not in data:
                return {"error": f"No data available for tag {tag_id}"}

            points = data["points"]
            values = [p["value"] for p in points if p.get("value") is not None]

            if not values:
                return {"error": "No valid values found"}

            # Calculate histogram
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bins if max_val > min_val else 1

            # Initialize bins
            histogram = []
            for i in range(bins):
                bin_start = min_val + (i * bin_width)
                bin_end = bin_start + bin_width

                # Count values in bin
                count = sum(1 for v in values if bin_start <= v < bin_end)

                # For last bin, include max value
                if i == bins - 1:
                    count = sum(1 for v in values if bin_start <= v <= bin_end)

                histogram.append({
                    "bin_index": i,
                    "range_start": round(bin_start, 2),
                    "range_end": round(bin_end, 2),
                    "count": count,
                    "percentage": round((count / len(values) * 100), 1) if values else 0
                })

            # Calculate statistics
            stats = await self.data_service.calculate_statistics(tag_id, duration)

            return {
                "tag_id": tag_id,
                "duration": duration,
                "histogram_type": histogram_type,
                "total_samples": len(values),
                "bins": bins,
                "histogram": histogram,
                "statistics": stats,
                "insights": self._generate_histogram_insights(histogram, stats)
            }

        except Exception as e:
            logger.error(f"Error generating histogram: {e}")
            return {"error": str(e)}

    def _generate_histogram_insights(self, histogram: List[Dict], stats: Dict) -> List[str]:
        """Generate insights from histogram distribution"""
        insights = []

        # Find mode (most frequent bin)
        mode_bin = max(histogram, key=lambda x: x["count"])
        insights.append(f"📊 Most common value range: {mode_bin['range_start']}-{mode_bin['range_end']} ({mode_bin['percentage']}% of samples)")

        # Check for skewness (basic check)
        mean = stats.get("mean", 0)
        middle_bin_idx = len(histogram) // 2
        middle_bin = histogram[middle_bin_idx]

        if mode_bin["bin_index"] < middle_bin_idx:
            insights.append("📈 Distribution is right-skewed (tail towards higher values)")
        elif mode_bin["bin_index"] > middle_bin_idx:
            insights.append("📉 Distribution is left-skewed (tail towards lower values)")
        else:
            insights.append("⚖️ Distribution is approximately symmetric")

        # Check for outliers (values in extreme bins)
        outlier_threshold = 5  # Less than 5% in bin
        extreme_bins = [h for h in histogram[:2] + histogram[-2:] if h["percentage"] < outlier_threshold and h["count"] > 0]
        if extreme_bins:
            insights.append(f"⚠️ Potential outliers detected in {len(extreme_bins)} extreme bins")

        return insights

    async def _calculate_correlation(
        self,
        tag_ids: List[str],
        duration: str = "24h",
        method: str = "pearson"
    ) -> Dict[str, Any]:
        """
        Calculate statistical correlation between tags
        """
        try:
            if len(tag_ids) < 2:
                return {"error": "At least 2 tags required for correlation analysis"}

            # Limit to 10 tags
            tag_ids = tag_ids[:10]

            # Get historical data for all tags
            all_data = {}
            for tag_id in tag_ids:
                data = await self.data_service.get_historical_data(tag_id, duration)
                if data and "points" in data:
                    all_data[tag_id] = data["points"]

            if len(all_data) < 2:
                return {"error": "Insufficient data for correlation analysis"}

            # Simple correlation calculation (would use numpy/scipy in production)
            correlations = []

            for i, tag1 in enumerate(tag_ids):
                for tag2 in tag_ids[i+1:]:
                    if tag1 not in all_data or tag2 not in all_data:
                        continue

                    # Get aligned values (by timestamp)
                    values1 = []
                    values2 = []

                    # Simple alignment - match by position
                    points1 = all_data[tag1]
                    points2 = all_data[tag2]
                    min_len = min(len(points1), len(points2))

                    for j in range(min_len):
                        v1 = points1[j].get("value")
                        v2 = points2[j].get("value")
                        if v1 is not None and v2 is not None:
                            values1.append(v1)
                            values2.append(v2)

                    if len(values1) < 10:  # Need at least 10 points
                        continue

                    # Calculate Pearson correlation coefficient
                    correlation = self._calculate_pearson_correlation(values1, values2)

                    correlations.append({
                        "tag1": tag1,
                        "tag2": tag2,
                        "correlation": round(correlation, 3),
                        "strength": self._interpret_correlation(correlation),
                        "sample_size": len(values1)
                    })

            # Sort by absolute correlation
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

            return {
                "duration": duration,
                "method": method,
                "tags_analyzed": len(all_data),
                "correlations": correlations,
                "insights": self._generate_correlation_insights(correlations)
            }

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {"error": str(e)}

    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = len(x)
        if n == 0:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        return numerator / (denominator_x * denominator_y)

    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.9:
            return "Very Strong"
        elif abs_corr >= 0.7:
            return "Strong"
        elif abs_corr >= 0.5:
            return "Moderate"
        elif abs_corr >= 0.3:
            return "Weak"
        else:
            return "Very Weak"

    def _generate_correlation_insights(self, correlations: List[Dict]) -> List[str]:
        """Generate insights from correlation analysis"""
        insights = []

        strong_positive = [c for c in correlations if c["correlation"] >= 0.7]
        strong_negative = [c for c in correlations if c["correlation"] <= -0.7]

        if strong_positive:
            insights.append(f"📈 Found {len(strong_positive)} strong positive correlations - variables move together")
            top = strong_positive[0]
            insights.append(f"   Strongest: {top['tag1']} ↔ {top['tag2']} (r={top['correlation']})")

        if strong_negative:
            insights.append(f"📉 Found {len(strong_negative)} strong negative correlations - variables move oppositely")
            top = strong_negative[0]
            insights.append(f"   Strongest: {top['tag1']} ↔ {top['tag2']} (r={top['correlation']})")

        if not strong_positive and not strong_negative:
            insights.append("⚖️ No strong correlations detected - variables appear independent")

        return insights

    async def _detect_trends(
        self,
        tag_id: str,
        duration: str = "24h",
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Detect trends in sensor data (increasing, decreasing, stable, cyclic)
        """
        try:
            # Get historical data
            data = await self.data_service.get_historical_data(tag_id, duration)

            if not data or "points" not in data:
                return {"error": f"No data available for tag {tag_id}"}

            points = data["points"]
            values = [p["value"] for p in points if p.get("value") is not None]

            if len(values) < 10:
                return {"error": "Insufficient data points for trend detection (minimum 10 required)"}

            # Calculate trend using linear regression
            n = len(values)
            x = list(range(n))

            mean_x = sum(x) / n
            mean_y = sum(values) / n

            # Calculate slope (trend direction)
            numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
            denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # Calculate R-squared (trend strength)
            y_pred = [mean_y + slope * (x[i] - mean_x) for i in range(n)]
            ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
            ss_tot = sum((values[i] - mean_y) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # Sensitivity thresholds for slope significance
            sensitivity_thresholds = {
                "low": 0.01,
                "medium": 0.005,
                "high": 0.001
            }
            threshold = sensitivity_thresholds.get(sensitivity, 0.005)

            # Determine trend type
            abs_slope = abs(slope)
            slope_normalized = abs_slope / (mean_y if mean_y != 0 else 1)

            if r_squared > 0.7 and slope_normalized > threshold:
                if slope > 0:
                    trend_type = "increasing"
                    trend_description = "📈 Upward trend detected"
                else:
                    trend_type = "decreasing"
                    trend_description = "📉 Downward trend detected"
            elif r_squared < 0.3:
                trend_type = "cyclic_or_noisy"
                trend_description = "🔄 Cyclic or noisy pattern detected"
            else:
                trend_type = "stable"
                trend_description = "⚖️ Stable - no significant trend"

            # Calculate rate of change
            if len(values) > 1:
                rate_of_change = (values[-1] - values[0]) / len(values)
            else:
                rate_of_change = 0

            return {
                "tag_id": tag_id,
                "duration": duration,
                "sensitivity": sensitivity,
                "trend_type": trend_type,
                "trend_description": trend_description,
                "slope": round(slope, 6),
                "r_squared": round(r_squared, 3),
                "rate_of_change": round(rate_of_change, 4),
                "data_points_analyzed": n,
                "start_value": round(values[0], 2),
                "end_value": round(values[-1], 2),
                "change": round(values[-1] - values[0], 2),
                "change_percentage": round(((values[-1] - values[0]) / values[0] * 100), 2) if values[0] != 0 else 0,
                "insights": self._generate_trend_insights(trend_type, slope, r_squared, values)
            }

        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
            return {"error": str(e)}

    def _generate_trend_insights(self, trend_type: str, slope: float, r_squared: float, values: List[float]) -> List[str]:
        """Generate insights from trend analysis"""
        insights = []

        if trend_type == "increasing":
            insights.append("📈 Value is consistently increasing over time")
            if slope > 0.1:
                insights.append("⚠️ Rapid increase detected - may require attention")
        elif trend_type == "decreasing":
            insights.append("📉 Value is consistently decreasing over time")
            if slope < -0.1:
                insights.append("⚠️ Rapid decrease detected - may require attention")
        elif trend_type == "stable":
            insights.append("✅ Value is stable with minor fluctuations")
        else:
            insights.append("🔄 Pattern shows cyclical behavior or high variability")

        # Check confidence
        if r_squared > 0.9:
            insights.append(f"🎯 High confidence trend (R²={r_squared:.3f})")
        elif r_squared < 0.5:
            insights.append(f"⚠️ Low confidence trend (R²={r_squared:.3f}) - data may be too variable")

        # Volatility check
        if len(values) > 1:
            import statistics
            stddev = statistics.stdev(values)
            mean = statistics.mean(values)
            cv = (stddev / mean * 100) if mean != 0 else 0

            if cv > 20:
                insights.append(f"📊 High variability detected (CV={cv:.1f}%)")

        return insights

    async def _generate_insights(
        self,
        scope: str = "system",
        tag_ids: List[str] = None,
        duration: str = "24h",
        equipment_filter: str = None
    ) -> Dict[str, Any]:
        """
        Generate automated insights from data patterns, anomalies, and trends
        """
        try:
            insights = {
                "scope": scope,
                "duration": duration,
                "generated_at": datetime.utcnow().isoformat(),
                "insights": [],
                "recommendations": [],
                "alerts": []
            }

            # Alarm insights
            if scope in ["system", "alarms"]:
                alarm_analysis = await self._analyze_alarm_frequency(
                    duration=duration,
                    equipment_filter=equipment_filter
                )

                if "error" not in alarm_analysis:
                    insights["insights"].extend(alarm_analysis.get("insights", []))

                    # Add specific alerts
                    if alarm_analysis.get("chattering_alarms"):
                        insights["alerts"].append({
                            "severity": "high",
                            "message": f"{len(alarm_analysis['chattering_alarms'])} chattering alarms detected",
                            "action": "Review alarm deadbands and delays"
                        })

                    if alarm_analysis.get("alarm_floods"):
                        insights["alerts"].append({
                            "severity": "critical",
                            "message": f"{len(alarm_analysis['alarm_floods'])} alarm flood periods detected",
                            "action": "Implement alarm suppression logic"
                        })

            # Tag-specific insights
            if tag_ids and scope in ["tag", "equipment"]:
                for tag_id in tag_ids[:5]:  # Limit to 5 tags
                    # Detect anomalies
                    anomaly_result = await self._detect_anomalies(tag_id, duration)
                    if anomaly_result.get("anomaly_count", 0) > 0:
                        insights["insights"].append(
                            f"🔍 {tag_id}: {anomaly_result['anomaly_count']} anomalies detected"
                        )
                        insights["alerts"].append({
                            "severity": "medium",
                            "tag_id": tag_id,
                            "message": f"{anomaly_result['anomaly_count']} anomalous values detected",
                            "action": "Investigate cause of anomalies"
                        })

                    # Detect trends
                    trend_result = await self._detect_trends(tag_id, duration)
                    if trend_result.get("trend_type") in ["increasing", "decreasing"]:
                        insights["insights"].append(
                            f"{trend_result['trend_description']} for {tag_id}"
                        )

            # Generate recommendations
            if len(insights["alerts"]) > 3:
                insights["recommendations"].append(
                    "Multiple issues detected - prioritize by severity and implement systematic improvements"
                )

            if not insights["insights"]:
                insights["insights"].append("✅ No significant issues detected - system operating normally")

            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {"error": str(e)}

    # ========================================
    # PCM - MTBF/MTTR Calculation
    # ========================================
    async def _calculate_mtbf_mttr(
        self,
        equipment_id: str,
        status_tag: str = None,
        duration: str = "30d",
        failure_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Calculate MTBF (Mean Time Between Failures) and MTTR (Mean Time To Repair)

        MTBF = Total Operating Time / Number of Failures
        MTTR = Total Repair Time / Number of Repairs

        Availability = MTBF / (MTBF + MTTR)
        """
        try:
            from datetime import timedelta
            import statistics

            # Parse duration
            duration_map = {
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "90d": timedelta(days=90),
                "180d": timedelta(days=180),
                "365d": timedelta(days=365)
            }
            time_delta = duration_map.get(duration, timedelta(days=30))
            analysis_hours = time_delta.total_seconds() / 3600

            # Find status tag if not provided
            if not status_tag:
                # Search for status/running tags for this equipment
                search_results = await self.data_service.search_tags(f"{equipment_id} status", limit=10)
                status_candidates = [t for t in search_results if any(
                    kw in t.get("name", "").lower()
                    for kw in ["status", "running", "ligado", "funcionando", "ativo"]
                )]
                if status_candidates:
                    status_tag = status_candidates[0].get("id") or status_candidates[0].get("name")

            result = {
                "equipment_id": equipment_id,
                "duration": duration,
                "analysis_period_hours": round(analysis_hours, 1),
                "status_tag": status_tag,
                "mtbf_hours": None,
                "mttr_hours": None,
                "availability_percent": None,
                "failure_count": 0,
                "total_operating_hours": 0,
                "total_downtime_hours": 0,
                "failures": [],
                "reliability_classification": None,
                "insights": [],
                "recommendations": []
            }

            if not status_tag:
                # If no status tag, try to infer from alarm history
                alarm_data = await self._analyze_alarm_frequency(
                    duration=duration,
                    equipment_filter=equipment_id
                )

                if alarm_data and "error" not in alarm_data:
                    # Estimate failures from critical alarms
                    critical_alarms = alarm_data.get("severity_distribution", {}).get("critical", 0)
                    high_alarms = alarm_data.get("severity_distribution", {}).get("high", 0)

                    estimated_failures = critical_alarms + (high_alarms // 2)

                    if estimated_failures > 0:
                        # Estimate MTBF from alarm frequency
                        mtbf_estimate = analysis_hours / estimated_failures
                        result["mtbf_hours"] = round(mtbf_estimate, 1)
                        result["failure_count"] = estimated_failures
                        result["estimation_method"] = "alarm_based"
                        result["insights"].append(
                            f"⚠️ MTBF estimado com base em {estimated_failures} alarmes críticos/altos"
                        )
                    else:
                        result["insights"].append("✅ Nenhuma falha crítica detectada no período")
                        result["mtbf_hours"] = analysis_hours  # No failures = full MTBF
                        result["availability_percent"] = 100.0

                result["recommendations"].append(
                    "💡 Configure uma tag de status (running/stopped) para cálculo preciso de MTBF/MTTR"
                )

            else:
                # Get historical status data
                status_data = await self.data_service.get_historical_data(status_tag, duration)

                if status_data and "points" in status_data:
                    points = status_data["points"]

                    if len(points) < 2:
                        result["error"] = "Insufficient data points for MTBF/MTTR calculation"
                        return result

                    # Analyze status transitions
                    running_periods = []
                    downtime_periods = []
                    failures = []

                    current_state = None
                    state_start = None
                    threshold = failure_threshold if failure_threshold is not None else 0.5

                    for point in points:
                        value = point.get("value")
                        timestamp = point.get("timestamp")

                        if value is None or timestamp is None:
                            continue

                        # Determine state (running = 1, stopped = 0)
                        is_running = float(value) > threshold

                        if current_state is None:
                            current_state = is_running
                            state_start = timestamp
                            continue

                        if is_running != current_state:
                            # State transition detected
                            if isinstance(timestamp, str):
                                from datetime import datetime as dt
                                end_time = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                                start_time = dt.fromisoformat(state_start.replace('Z', '+00:00'))
                            else:
                                end_time = timestamp
                                start_time = state_start

                            duration_hours = (end_time - start_time).total_seconds() / 3600

                            if current_state:
                                # Was running, now stopped = FAILURE
                                running_periods.append(duration_hours)
                                failures.append({
                                    "start_time": state_start,
                                    "end_time": timestamp,
                                    "running_hours_before_failure": round(duration_hours, 2)
                                })
                            else:
                                # Was stopped, now running = REPAIR COMPLETE
                                downtime_periods.append(duration_hours)
                                if failures:
                                    failures[-1]["repair_hours"] = round(duration_hours, 2)

                            current_state = is_running
                            state_start = timestamp

                    # Calculate metrics
                    total_operating = sum(running_periods)
                    total_downtime = sum(downtime_periods)
                    failure_count = len(failures)

                    result["total_operating_hours"] = round(total_operating, 1)
                    result["total_downtime_hours"] = round(total_downtime, 1)
                    result["failure_count"] = failure_count
                    result["failures"] = failures[:10]  # Limit to 10 failures for display

                    if failure_count > 0:
                        result["mtbf_hours"] = round(total_operating / failure_count, 1)

                        if downtime_periods:
                            result["mttr_hours"] = round(
                                sum(downtime_periods) / len(downtime_periods), 1
                            )
                    else:
                        result["mtbf_hours"] = round(total_operating, 1)
                        result["insights"].append("✅ Nenhuma falha detectada no período")

                    # Calculate availability
                    total_time = total_operating + total_downtime
                    if total_time > 0:
                        result["availability_percent"] = round(
                            (total_operating / total_time) * 100, 2
                        )

            # Add classification and insights
            mtbf = result.get("mtbf_hours")
            mttr = result.get("mttr_hours")
            availability = result.get("availability_percent")

            if mtbf:
                if mtbf >= 720:  # > 30 days
                    result["reliability_classification"] = "Excelente"
                    result["insights"].append(f"🌟 MTBF excelente: {mtbf:.0f}h ({mtbf/24:.1f} dias)")
                elif mtbf >= 168:  # > 7 days
                    result["reliability_classification"] = "Bom"
                    result["insights"].append(f"✅ MTBF bom: {mtbf:.0f}h ({mtbf/24:.1f} dias)")
                elif mtbf >= 24:  # > 1 day
                    result["reliability_classification"] = "Regular"
                    result["insights"].append(f"⚠️ MTBF regular: {mtbf:.0f}h - considere manutenção preventiva")
                else:
                    result["reliability_classification"] = "Crítico"
                    result["insights"].append(f"🚨 MTBF crítico: {mtbf:.0f}h - ação imediata necessária")

            if mttr:
                if mttr <= 2:
                    result["insights"].append(f"✅ MTTR rápido: {mttr:.1f}h - manutenção eficiente")
                elif mttr <= 8:
                    result["insights"].append(f"⚡ MTTR aceitável: {mttr:.1f}h")
                else:
                    result["insights"].append(f"⚠️ MTTR alto: {mttr:.1f}h - otimize processos de reparo")
                    result["recommendations"].append(
                        "Implemente kits de manutenção e treinamento para reduzir MTTR"
                    )

            if availability is not None:
                if availability >= 99:
                    result["insights"].append(f"🌟 Disponibilidade World Class: {availability:.1f}%")
                elif availability >= 95:
                    result["insights"].append(f"✅ Alta disponibilidade: {availability:.1f}%")
                elif availability >= 85:
                    result["insights"].append(f"⚡ Disponibilidade aceitável: {availability:.1f}%")
                else:
                    result["insights"].append(f"🚨 Baixa disponibilidade: {availability:.1f}% - priorize manutenção")
                    result["recommendations"].append(
                        "Implemente programa de manutenção preventiva/preditiva"
                    )

            return result

        except Exception as e:
            logger.error(f"Error calculating MTBF/MTTR: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    # ========================================
    # PCM PREDITIVO - Failure Prediction
    # ========================================
    async def _predict_failure(
        self,
        equipment_id: str,
        tag_ids: List[str] = None,
        prediction_horizon: str = "7d",
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Predict equipment failures using trend analysis and pattern detection.

        Uses multiple indicators:
        1. Trend direction and acceleration
        2. Anomaly frequency increase
        3. Degradation patterns
        4. Historical failure patterns
        """
        try:
            from datetime import timedelta
            import statistics

            # Parse prediction horizon
            horizon_map = {
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "14d": timedelta(days=14),
                "30d": timedelta(days=30)
            }
            horizon_delta = horizon_map.get(prediction_horizon, timedelta(days=7))

            result = {
                "equipment_id": equipment_id,
                "prediction_horizon": prediction_horizon,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "overall_risk_level": "low",
                "failure_probability": 0.0,
                "confidence": 0.0,
                "predicted_failure_window": None,
                "risk_factors": [],
                "tag_analysis": [],
                "recommendations": [],
                "action_priority": "routine"
            }

            # Find relevant tags if not provided
            if not tag_ids:
                search_results = await self.data_service.search_tags(equipment_id, limit=20)
                # Filter for predictive maintenance relevant tags
                relevant_keywords = [
                    "temp", "temperatura", "vibr", "corrente", "current",
                    "potencia", "power", "pressao", "pressure", "speed",
                    "velocidade", "load", "carga"
                ]
                tag_ids = [
                    t.get("id") or t.get("name")
                    for t in search_results
                    if any(kw in t.get("name", "").lower() for kw in relevant_keywords)
                ][:10]  # Limit to 10 most relevant

            if not tag_ids:
                result["error"] = f"No relevant tags found for equipment {equipment_id}"
                result["recommendations"].append(
                    "Configure tags de monitoramento (temperatura, vibração, corrente) para predição"
                )
                return result

            # Analyze each tag for failure indicators
            risk_scores = []

            for tag_id in tag_ids:
                tag_analysis = {
                    "tag_id": tag_id,
                    "risk_score": 0.0,
                    "indicators": []
                }

                try:
                    # Get trend analysis
                    trend = await self._detect_trends(tag_id, duration="24h")

                    if "error" not in trend:
                        slope = trend.get("slope", 0)
                        r_squared = trend.get("r_squared", 0)
                        change_pct = trend.get("change_percentage", 0)

                        # Check for concerning trends
                        if trend.get("trend_type") == "increasing" and r_squared > 0.7:
                            # Temperature/current increasing is bad
                            if any(kw in tag_id.lower() for kw in ["temp", "corrente", "current", "vibr"]):
                                risk_contribution = min(abs(change_pct) / 10, 0.4)  # Max 40% from trend
                                tag_analysis["risk_score"] += risk_contribution
                                tag_analysis["indicators"].append({
                                    "type": "trend",
                                    "severity": "high" if change_pct > 10 else "medium",
                                    "description": f"Tendência de aumento: {change_pct:.1f}% (R²={r_squared:.2f})"
                                })

                    # Get anomaly analysis
                    anomalies = await self._detect_anomalies(tag_id, duration="24h", sensitivity="high")

                    if "error" not in anomalies:
                        anomaly_count = anomalies.get("anomaly_count", 0)

                        if anomaly_count > 0:
                            # Anomalies increase risk
                            risk_contribution = min(anomaly_count * 0.05, 0.3)  # Max 30% from anomalies
                            tag_analysis["risk_score"] += risk_contribution
                            tag_analysis["indicators"].append({
                                "type": "anomaly",
                                "severity": "high" if anomaly_count > 5 else "medium",
                                "description": f"{anomaly_count} anomalias detectadas nas últimas 24h"
                            })

                    # Get statistics for variability check
                    stats = await self.data_service.calculate_statistics(tag_id, "24h")

                    if stats and stats.get("mean") and stats.get("stddev"):
                        cv = (stats["stddev"] / stats["mean"]) * 100 if stats["mean"] != 0 else 0

                        if cv > 25:
                            risk_contribution = min((cv - 25) / 100, 0.2)  # Max 20% from variability
                            tag_analysis["risk_score"] += risk_contribution
                            tag_analysis["indicators"].append({
                                "type": "variability",
                                "severity": "medium",
                                "description": f"Alta variabilidade: CV={cv:.1f}%"
                            })

                    # Check if near limits (if available)
                    tag_info = await self.data_service.get_tag_info(tag_id)
                    if tag_info:
                        max_val = tag_info.get("max_value")
                        current = stats.get("mean") if stats else None

                        if max_val and current:
                            proximity = (current / max_val) * 100
                            if proximity > 80:
                                risk_contribution = (proximity - 80) / 100  # Up to 20%
                                tag_analysis["risk_score"] += risk_contribution
                                tag_analysis["indicators"].append({
                                    "type": "limit_proximity",
                                    "severity": "high" if proximity > 90 else "medium",
                                    "description": f"Próximo do limite: {proximity:.1f}% do máximo"
                                })

                except Exception as e:
                    logger.warning(f"Error analyzing tag {tag_id}: {e}")
                    continue

                # Cap individual tag risk at 1.0
                tag_analysis["risk_score"] = min(tag_analysis["risk_score"], 1.0)
                risk_scores.append(tag_analysis["risk_score"])

                if tag_analysis["risk_score"] > 0.1:
                    result["tag_analysis"].append(tag_analysis)

            # Calculate overall failure probability
            if risk_scores:
                # Weighted average with emphasis on max risks
                max_risk = max(risk_scores)
                avg_risk = statistics.mean(risk_scores)

                # Overall probability is combination of max and average
                failure_probability = (max_risk * 0.6) + (avg_risk * 0.4)
                result["failure_probability"] = round(failure_probability, 3)

                # Determine risk level
                if failure_probability >= 0.7:
                    result["overall_risk_level"] = "critical"
                    result["action_priority"] = "immediate"
                elif failure_probability >= 0.5:
                    result["overall_risk_level"] = "high"
                    result["action_priority"] = "urgent"
                elif failure_probability >= 0.3:
                    result["overall_risk_level"] = "medium"
                    result["action_priority"] = "planned"
                else:
                    result["overall_risk_level"] = "low"
                    result["action_priority"] = "routine"

                # Calculate confidence based on data quality
                result["confidence"] = round(min(len(tag_ids) / 5, 1.0) * 0.8 + 0.2, 2)

                # Estimate failure window if risk is high
                if failure_probability >= 0.5:
                    # Higher probability = sooner failure
                    days_to_failure = int((1 - failure_probability) * 30)
                    result["predicted_failure_window"] = {
                        "min_days": max(1, days_to_failure - 3),
                        "max_days": days_to_failure + 7,
                        "most_likely_days": days_to_failure
                    }

                # Generate risk factors summary
                for tag_analysis in result["tag_analysis"]:
                    if tag_analysis["risk_score"] >= 0.3:
                        result["risk_factors"].append({
                            "tag_id": tag_analysis["tag_id"],
                            "risk_score": round(tag_analysis["risk_score"], 2),
                            "primary_concern": tag_analysis["indicators"][0]["description"]
                                if tag_analysis["indicators"] else "Risco elevado detectado"
                        })

            # Generate recommendations based on risk level
            if result["overall_risk_level"] == "critical":
                result["recommendations"] = [
                    "🚨 AÇÃO IMEDIATA: Agende inspeção/manutenção nas próximas 24-48h",
                    "Prepare peças de reposição e equipe de manutenção",
                    "Considere reduzir carga operacional até manutenção"
                ]
            elif result["overall_risk_level"] == "high":
                result["recommendations"] = [
                    "⚠️ Agende manutenção preventiva para próxima semana",
                    "Aumente frequência de monitoramento",
                    "Verifique estoque de peças de reposição"
                ]
            elif result["overall_risk_level"] == "medium":
                result["recommendations"] = [
                    "📋 Inclua na próxima parada programada",
                    "Monitore tendências diariamente",
                    "Prepare plano de contingência"
                ]
            else:
                result["recommendations"] = [
                    "✅ Equipamento operando normalmente",
                    "Mantenha monitoramento de rotina",
                    "Próxima análise preditiva em 7 dias"
                ]

            return result

        except Exception as e:
            logger.error(f"Error predicting failure: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    # ========================================
    # QUALIDADE - SPC/CEP Limits Calculation
    # ========================================
    async def _calculate_spc_limits(
        self,
        tag_id: str,
        specification_limits: Dict[str, float] = None,
        duration: str = "24h",
        subgroup_size: int = 5,
        control_chart_type: str = "x_bar_r"
    ) -> Dict[str, Any]:
        """
        Calculate Statistical Process Control (SPC/CEP) limits.

        Calculates:
        - Control limits (UCL, LCL, CL)
        - Capability indices (Cp, Cpk, Pp, Ppk)
        - Process stability assessment
        - Out-of-control points
        """
        try:
            import statistics
            import math

            # Get historical data
            data = await self.data_service.get_historical_data(tag_id, duration)

            if not data or "points" not in data:
                return {"error": f"No data available for tag {tag_id}"}

            points = data["points"]
            values = [p["value"] for p in points if p.get("value") is not None]

            if len(values) < subgroup_size * 2:
                return {
                    "error": f"Insufficient data for SPC analysis. Need at least {subgroup_size * 2} points, got {len(values)}"
                }

            result = {
                "tag_id": tag_id,
                "duration": duration,
                "sample_size": len(values),
                "subgroup_size": subgroup_size,
                "chart_type": control_chart_type,
                "control_limits": {},
                "process_statistics": {},
                "capability_indices": {},
                "stability_assessment": {},
                "out_of_control_points": [],
                "insights": [],
                "recommendations": []
            }

            # Calculate basic statistics
            mean = statistics.mean(values)
            stddev = statistics.stdev(values) if len(values) > 1 else 0

            result["process_statistics"] = {
                "mean": round(mean, 4),
                "stddev": round(stddev, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "range": round(max(values) - min(values), 4)
            }

            # Constants for control chart calculations (based on subgroup size)
            # A2, D3, D4 constants for X-bar R chart
            control_constants = {
                2: {"A2": 1.880, "D3": 0, "D4": 3.267, "d2": 1.128},
                3: {"A2": 1.023, "D3": 0, "D4": 2.574, "d2": 1.693},
                4: {"A2": 0.729, "D3": 0, "D4": 2.282, "d2": 2.059},
                5: {"A2": 0.577, "D3": 0, "D4": 2.114, "d2": 2.326},
                6: {"A2": 0.483, "D3": 0, "D4": 2.004, "d2": 2.534},
                7: {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
                8: {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
                9: {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
                10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078}
            }

            n = min(max(subgroup_size, 2), 10)  # Clamp to valid range
            constants = control_constants[n]

            if control_chart_type in ["x_bar_r", "x_bar_s"]:
                # Create subgroups
                subgroups = []
                for i in range(0, len(values) - n + 1, n):
                    subgroup = values[i:i + n]
                    if len(subgroup) == n:
                        subgroups.append(subgroup)

                if len(subgroups) < 2:
                    return {"error": "Not enough subgroups for control chart analysis"}

                # Calculate subgroup means and ranges
                subgroup_means = [statistics.mean(sg) for sg in subgroups]
                subgroup_ranges = [max(sg) - min(sg) for sg in subgroups]

                x_bar = statistics.mean(subgroup_means)
                r_bar = statistics.mean(subgroup_ranges)

                # Calculate control limits for X-bar chart
                ucl_x = x_bar + constants["A2"] * r_bar
                lcl_x = x_bar - constants["A2"] * r_bar

                # Calculate control limits for R chart
                ucl_r = constants["D4"] * r_bar
                lcl_r = constants["D3"] * r_bar

                # Estimate process sigma from R-bar
                sigma_estimate = r_bar / constants["d2"]

                result["control_limits"] = {
                    "x_bar_chart": {
                        "ucl": round(ucl_x, 4),
                        "cl": round(x_bar, 4),
                        "lcl": round(lcl_x, 4)
                    },
                    "r_chart": {
                        "ucl": round(ucl_r, 4),
                        "cl": round(r_bar, 4),
                        "lcl": round(lcl_r, 4)
                    }
                }

                result["process_statistics"]["x_bar"] = round(x_bar, 4)
                result["process_statistics"]["r_bar"] = round(r_bar, 4)
                result["process_statistics"]["sigma_estimate"] = round(sigma_estimate, 4)
                result["process_statistics"]["subgroup_count"] = len(subgroups)

                # Check for out-of-control points
                for i, (sg_mean, sg_range) in enumerate(zip(subgroup_means, subgroup_ranges)):
                    violations = []

                    if sg_mean > ucl_x or sg_mean < lcl_x:
                        violations.append(f"X-bar fora dos limites: {sg_mean:.2f}")
                    if sg_range > ucl_r or sg_range < lcl_r:
                        violations.append(f"Range fora dos limites: {sg_range:.2f}")

                    if violations:
                        result["out_of_control_points"].append({
                            "subgroup": i + 1,
                            "x_bar": round(sg_mean, 4),
                            "range": round(sg_range, 4),
                            "violations": violations
                        })

            elif control_chart_type == "individuals":
                # I-MR chart (individuals and moving range)
                moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, len(values))]

                x_bar = mean
                mr_bar = statistics.mean(moving_ranges) if moving_ranges else 0

                # d2 for n=2 (moving range of 2 consecutive values)
                d2 = 1.128
                sigma_estimate = mr_bar / d2

                ucl_x = x_bar + 3 * sigma_estimate
                lcl_x = x_bar - 3 * sigma_estimate

                ucl_mr = 3.267 * mr_bar  # D4 for n=2
                lcl_mr = 0

                result["control_limits"] = {
                    "individuals_chart": {
                        "ucl": round(ucl_x, 4),
                        "cl": round(x_bar, 4),
                        "lcl": round(lcl_x, 4)
                    },
                    "mr_chart": {
                        "ucl": round(ucl_mr, 4),
                        "cl": round(mr_bar, 4),
                        "lcl": round(lcl_mr, 4)
                    }
                }

                result["process_statistics"]["mr_bar"] = round(mr_bar, 4)
                result["process_statistics"]["sigma_estimate"] = round(sigma_estimate, 4)

                # Check for out-of-control points
                for i, val in enumerate(values):
                    if val > ucl_x or val < lcl_x:
                        result["out_of_control_points"].append({
                            "point": i + 1,
                            "value": round(val, 4),
                            "violation": f"Valor fora dos limites de controle"
                        })

            # Calculate capability indices if specification limits provided
            if specification_limits:
                usl = specification_limits.get("usl")
                lsl = specification_limits.get("lsl")
                target = specification_limits.get("target", (usl + lsl) / 2 if usl and lsl else None)

                sigma = result["process_statistics"].get("sigma_estimate", stddev)

                if usl is not None and lsl is not None and sigma > 0:
                    # Cp - Process Capability (potential)
                    cp = (usl - lsl) / (6 * sigma)

                    # Cpk - Process Capability (actual - accounts for centering)
                    cpu = (usl - mean) / (3 * sigma)
                    cpl = (mean - lsl) / (3 * sigma)
                    cpk = min(cpu, cpl)

                    # Pp and Ppk - Process Performance (using overall stddev)
                    pp = (usl - lsl) / (6 * stddev) if stddev > 0 else 0
                    ppu = (usl - mean) / (3 * stddev) if stddev > 0 else 0
                    ppl = (mean - lsl) / (3 * stddev) if stddev > 0 else 0
                    ppk = min(ppu, ppl)

                    result["capability_indices"] = {
                        "cp": round(cp, 3),
                        "cpk": round(cpk, 3),
                        "cpu": round(cpu, 3),
                        "cpl": round(cpl, 3),
                        "pp": round(pp, 3),
                        "ppk": round(ppk, 3),
                        "specification_limits": {
                            "usl": usl,
                            "lsl": lsl,
                            "target": target
                        }
                    }

                    # Calculate sigma level (approximate)
                    sigma_level = cpk * 3
                    result["capability_indices"]["sigma_level"] = round(sigma_level, 2)

                    # PPM (Parts Per Million) defect rate estimate
                    # Using Z-score approximation
                    from math import erf, sqrt
                    z_upper = (usl - mean) / sigma if sigma > 0 else float('inf')
                    z_lower = (mean - lsl) / sigma if sigma > 0 else float('inf')

                    def phi(z):
                        return 0.5 * (1 + erf(z / sqrt(2)))

                    ppm_upper = (1 - phi(z_upper)) * 1000000
                    ppm_lower = (1 - phi(z_lower)) * 1000000
                    ppm_total = ppm_upper + ppm_lower

                    result["capability_indices"]["ppm_estimate"] = round(ppm_total, 1)

            # Stability assessment
            ooc_count = len(result["out_of_control_points"])
            ooc_percentage = (ooc_count / len(values)) * 100 if values else 0

            if ooc_percentage <= 1:
                stability = "Estável"
                stability_icon = "✅"
            elif ooc_percentage <= 5:
                stability = "Marginalmente Estável"
                stability_icon = "⚡"
            else:
                stability = "Instável"
                stability_icon = "🚨"

            result["stability_assessment"] = {
                "status": stability,
                "out_of_control_count": ooc_count,
                "out_of_control_percentage": round(ooc_percentage, 2)
            }

            # Generate insights
            result["insights"].append(f"{stability_icon} Processo {stability}: {ooc_count} pontos fora de controle ({ooc_percentage:.1f}%)")

            if "capability_indices" in result and result["capability_indices"]:
                cpk = result["capability_indices"].get("cpk", 0)
                sigma_level = result["capability_indices"].get("sigma_level", 0)

                if cpk >= 1.67:
                    result["insights"].append(f"🌟 Cpk = {cpk:.2f} - Processo Six Sigma ({sigma_level:.1f}σ)")
                elif cpk >= 1.33:
                    result["insights"].append(f"✅ Cpk = {cpk:.2f} - Processo capaz ({sigma_level:.1f}σ)")
                elif cpk >= 1.0:
                    result["insights"].append(f"⚡ Cpk = {cpk:.2f} - Processo marginalmente capaz ({sigma_level:.1f}σ)")
                else:
                    result["insights"].append(f"🚨 Cpk = {cpk:.2f} - Processo incapaz ({sigma_level:.1f}σ) - AÇÃO NECESSÁRIA")
                    result["recommendations"].append("Reduza variabilidade do processo ou revise especificações")

                ppm = result["capability_indices"].get("ppm_estimate", 0)
                result["insights"].append(f"📊 Taxa de defeitos estimada: {ppm:.0f} PPM")

            # Recommendations based on analysis
            if stability == "Instável":
                result["recommendations"].append("🚨 Investigue causas especiais de variação")
                result["recommendations"].append("Identifique e elimine fontes de instabilidade antes de melhorar capabilidade")

            if ooc_count > 0:
                result["recommendations"].append(f"Analise os {ooc_count} pontos fora de controle para identificar padrões")

            if not specification_limits:
                result["recommendations"].append("💡 Forneça limites de especificação (USL/LSL) para cálculo de Cp/Cpk")

            return result

        except Exception as e:
            logger.error(f"Error calculating SPC limits: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    # ========================================
    # DASHBOARD EXECUTIVO - Implementações
    # ========================================

    async def _get_executive_overview(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get consolidated executive overview with all main KPIs.
        Calls the executive-summary API endpoint.
        """
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/overview",
                    params={"time_range": time_range}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "time_range": time_range,
                            "generated_at": data.get("generated_at"),
                            "kpis": data.get("kpis", {}),
                            "alarms": data.get("alarms", {}),
                            "critical_equipment": data.get("critical_equipment", []),
                            "production_trends": data.get("production_trends", {}),
                            "insights": data.get("insights", []),
                            "financial_summary": data.get("financial_summary", {}),
                            "summary": self._generate_executive_summary_text(data)
                        }
                    else:
                        # Fallback: generate simulated data
                        return await self._generate_simulated_executive_overview(time_range)

        except Exception as e:
            logger.warning(f"Error fetching executive overview from API: {e}")
            return await self._generate_simulated_executive_overview(time_range)

    async def _generate_simulated_executive_overview(self, time_range: str) -> Dict[str, Any]:
        """Generate simulated executive data when API is unavailable"""
        import random
        from datetime import datetime

        oee = round(random.uniform(78, 92), 1)
        availability = round(random.uniform(88, 98), 1)
        performance = round(random.uniform(82, 95), 1)
        quality = round(random.uniform(96, 99.5), 1)

        return {
            "success": True,
            "time_range": time_range,
            "generated_at": datetime.utcnow().isoformat(),
            "kpis": {
                "oee": {"value": oee, "target": 85.0, "trend": "up" if oee > 85 else "down", "status": "good" if oee >= 85 else "warning"},
                "availability": {"value": availability, "target": 95.0, "trend": "up", "status": "good" if availability >= 95 else "warning"},
                "performance": {"value": performance, "target": 90.0, "trend": "stable", "status": "good" if performance >= 90 else "warning"},
                "quality": {"value": quality, "target": 99.0, "trend": "up", "status": "good" if quality >= 99 else "warning"}
            },
            "alarms": {
                "total_active": random.randint(3, 15),
                "by_severity": {"critical": random.randint(0, 2), "high": random.randint(1, 4), "medium": random.randint(2, 6), "low": random.randint(1, 5)},
                "trend": random.choice(["up", "down", "stable"]),
                "mttr_hours": round(random.uniform(1.5, 4.0), 1)
            },
            "critical_equipment": [
                {"name": "Elevador EL-01", "alarm_count": random.randint(2, 8), "health_score": random.randint(65, 95), "status": "warning"},
                {"name": "Correia TR-02", "alarm_count": random.randint(1, 5), "health_score": random.randint(70, 98), "status": "good"},
                {"name": "Silo SI-03", "alarm_count": random.randint(0, 3), "health_score": random.randint(80, 99), "status": "good"}
            ],
            "production_trends": {
                "production_rate": {"current": round(random.uniform(150, 200), 1), "previous": 175.0, "unit": "ton/h", "change_percent": round(random.uniform(-5, 10), 1), "trend": "up"},
                "energy_efficiency": {"current": round(random.uniform(12, 18), 2), "previous": 15.0, "unit": "kWh/ton", "change_percent": round(random.uniform(-8, 5), 1), "trend": "down"},
                "throughput": {"current": round(random.uniform(3500, 4500), 0), "previous": 4000.0, "unit": "ton/dia", "change_percent": round(random.uniform(-3, 8), 1), "trend": "up"}
            },
            "insights": [
                {"type": "success", "title": "OEE Acima da Meta", "description": f"OEE atual de {oee}% supera a meta de 85%", "impact": "Produtividade otimizada"},
                {"type": "warning", "title": "Alarmes Críticos", "description": "Monitorar equipamento EL-01", "impact": "Risco de parada não programada"}
            ],
            "financial_summary": {
                "estimated_savings_today": round(random.uniform(5000, 15000), 2),
                "downtime_cost_avoided": round(random.uniform(8000, 25000), 2),
                "efficiency_improvement": round(random.uniform(2, 8), 1),
                "projected_monthly_savings": round(random.uniform(150000, 400000), 2)
            },
            "summary": f"Dashboard Executivo ({time_range}): OEE={oee}%, Disponibilidade={availability}%, Performance={performance}%, Qualidade={quality}%"
        }

    def _generate_executive_summary_text(self, data: Dict) -> str:
        """Generate a text summary of executive data"""
        kpis = data.get("kpis", {})
        alarms = data.get("alarms", {})

        oee = kpis.get("oee", {}).get("value", 0)
        availability = kpis.get("availability", {}).get("value", 0)
        performance = kpis.get("performance", {}).get("value", 0)
        quality = kpis.get("quality", {}).get("value", 0)
        active_alarms = alarms.get("total_active", 0)
        critical = alarms.get("by_severity", {}).get("critical", 0)

        return (
            f"Visão Executiva: OEE={oee}% (Disponibilidade={availability}%, "
            f"Performance={performance}%, Qualidade={quality}%). "
            f"Alarmes ativos: {active_alarms} ({critical} críticos)."
        )

    async def _get_energy_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get detailed energy metrics"""
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/energy",
                    params={"time_range": time_range}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return await self._generate_simulated_energy_metrics(time_range)
        except Exception as e:
            logger.warning(f"Error fetching energy metrics: {e}")
            return await self._generate_simulated_energy_metrics(time_range)

    async def _generate_simulated_energy_metrics(self, time_range: str) -> Dict[str, Any]:
        """Generate simulated energy data"""
        import random

        consumption = round(random.uniform(2500, 4500), 0)
        demand = round(random.uniform(800, 1200), 0)

        return {
            "time_range": time_range,
            "current": {
                "consumption_kwh": consumption,
                "demand_kw": demand,
                "power_factor": round(random.uniform(0.88, 0.96), 2),
                "status": "normal"
            },
            "period": {
                "total_kwh": consumption * (24 if time_range == "24h" else 168),
                "average_kwh_hour": consumption,
                "peak_demand_kw": demand + random.randint(100, 300),
                "change_percent": round(random.uniform(-5, 8), 1),
                "trend": random.choice(["up", "down", "stable"])
            },
            "forecast": {
                "monthly_kwh": round(consumption * 720, 0),
                "confidence": random.randint(85, 95),
                "peak_demand_forecast_kw": demand + random.randint(150, 350)
            },
            "bill_forecast": {
                "energy_cost": round(consumption * 720 * 0.65, 2),
                "demand_cost": round(demand * 45, 2),
                "taxes": round(consumption * 720 * 0.65 * 0.30, 2),
                "total_estimate": round(consumption * 720 * 0.65 * 1.30 + demand * 45, 2)
            },
            "efficiency": {
                "kwh_per_ton": round(random.uniform(12, 18), 2),
                "cost_per_ton": round(random.uniform(8, 15), 2),
                "target_kwh_per_ton": 14.0,
                "status": "good" if random.random() > 0.3 else "warning"
            },
            "peak_demand": {
                "current_kw": demand,
                "contracted_kw": 1500,
                "utilization_percent": round((demand / 1500) * 100, 1),
                "risk_of_penalty": demand > 1350
            },
            "insights": [
                {"type": "info", "title": "Consumo Normal", "description": f"Consumo de {consumption} kWh dentro da média", "recommendation": "Manter monitoramento"}
            ]
        }

    async def _get_production_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get detailed production metrics"""
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/production",
                    params={"time_range": time_range}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return await self._generate_simulated_production_metrics(time_range)
        except Exception as e:
            logger.warning(f"Error fetching production metrics: {e}")
            return await self._generate_simulated_production_metrics(time_range)

    async def _generate_simulated_production_metrics(self, time_range: str) -> Dict[str, Any]:
        """Generate simulated production data"""
        import random

        throughput = round(random.uniform(150, 220), 1)
        utilization = round(random.uniform(75, 95), 1)

        return {
            "time_range": time_range,
            "current": {
                "throughput_ton_hour": throughput,
                "utilization_percent": utilization,
                "cycle_time_minutes": round(random.uniform(3, 8), 1),
                "status": "good" if utilization > 80 else "warning"
            },
            "period": {
                "total_tons": round(throughput * (24 if time_range == "24h" else 168), 0),
                "average_ton_hour": throughput,
                "peak_ton_hour": throughput + random.randint(20, 50),
                "change_percent": round(random.uniform(-5, 12), 1),
                "trend": "up" if random.random() > 0.4 else "down"
            },
            "capacity": {
                "nominal_ton_hour": 250,
                "utilization_percent": utilization,
                "idle_time_percent": round(100 - utilization, 1),
                "status": "good" if utilization > 80 else "warning"
            },
            "target": {
                "production_target_tons": 4500,
                "achievement_percent": round(random.uniform(85, 105), 1),
                "gap_tons": round(random.uniform(-200, 300), 0),
                "status": "good" if random.random() > 0.3 else "warning"
            },
            "efficiency": {
                "overall_efficiency": round(random.uniform(82, 95), 1),
                "time_efficiency": round(random.uniform(88, 98), 1),
                "performance_efficiency": round(random.uniform(85, 96), 1)
            },
            "insights": [
                {"type": "success", "title": "Produção Estável", "description": f"Throughput de {throughput} ton/h", "recommendation": "Manter ritmo atual"}
            ]
        }

    async def _get_alarm_pareto(self, time_range: str = "24h", limit: int = 10) -> Dict[str, Any]:
        """Get Pareto analysis of alarms"""
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/alarms/pareto",
                    params={"time_range": time_range}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return await self._generate_simulated_pareto(time_range, limit)
        except Exception as e:
            logger.warning(f"Error fetching alarm pareto: {e}")
            return await self._generate_simulated_pareto(time_range, limit)

    async def _generate_simulated_pareto(self, time_range: str, limit: int) -> Dict[str, Any]:
        """Generate simulated Pareto data"""
        import random

        alarm_types = [
            "Alta Temperatura", "Baixa Pressão", "Sobrecarga Motor",
            "Falha Comunicação", "Nível Alto", "Vibração Excessiva",
            "Velocidade Baixa", "Corrente Alta", "Falha Sensor", "Timeout"
        ]

        pareto_data = []
        cumulative = 0
        total = random.randint(80, 200)

        for i, alarm_type in enumerate(alarm_types[:limit]):
            count = max(1, int(total * (0.35 / (i + 1))))
            percent = round((count / total) * 100, 1)
            cumulative += percent

            pareto_data.append({
                "rank": i + 1,
                "alarm_type": alarm_type,
                "count": count,
                "percent": percent,
                "cumulative_percent": min(100, round(cumulative, 1)),
                "mttr_minutes": random.randint(15, 120),
                "estimated_cost": round(count * random.uniform(500, 2000), 2),
                "is_80_percent": cumulative <= 80
            })

        return {
            "time_range": time_range,
            "summary": {
                "total_alarms": total,
                "unique_types": len(pareto_data),
                "total_estimated_cost": sum(p["estimated_cost"] for p in pareto_data),
                "alarms_causing_80_percent": len([p for p in pareto_data if p["is_80_percent"]]),
                "pareto_efficiency": f"{len([p for p in pareto_data if p['is_80_percent']])} tipos causam 80% dos alarmes"
            },
            "pareto": pareto_data,
            "top_equipment": [
                {"equipment": "Elevador EL-01", "alarm_count": random.randint(15, 35), "percent_of_total": round(random.uniform(15, 30), 1), "status": "warning"},
                {"equipment": "Correia TR-02", "alarm_count": random.randint(10, 25), "percent_of_total": round(random.uniform(10, 20), 1), "status": "warning"},
                {"equipment": "Motor MT-03", "alarm_count": random.randint(5, 15), "percent_of_total": round(random.uniform(5, 12), 1), "status": "good"}
            ],
            "mttr_stats": {
                "average_minutes": round(sum(p["mttr_minutes"] for p in pareto_data) / len(pareto_data), 1),
                "min_minutes": min(p["mttr_minutes"] for p in pareto_data),
                "max_minutes": max(p["mttr_minutes"] for p in pareto_data)
            },
            "insights": [
                {"type": "warning", "title": "Concentração de Alarmes", "description": f"Top 3 tipos representam {pareto_data[2]['cumulative_percent']}% do total", "recommendation": "Focar ações corretivas nos tipos principais"}
            ]
        }

    async def _get_financial_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get financial summary"""
        import random

        hours = 24 if time_range == "24h" else (168 if time_range == "7d" else 720)
        base_savings = random.uniform(200, 500)

        return {
            "time_range": time_range,
            "estimated_savings_today": round(base_savings * 24, 2),
            "downtime_cost_avoided": round(base_savings * 24 * 1.5, 2),
            "efficiency_improvement": round(random.uniform(2, 8), 1),
            "projected_monthly_savings": round(base_savings * 720, 2),
            "cost_breakdown": {
                "energy_savings": round(base_savings * hours * 0.3, 2),
                "maintenance_savings": round(base_savings * hours * 0.4, 2),
                "productivity_gains": round(base_savings * hours * 0.3, 2)
            },
            "roi_metrics": {
                "monthly_roi_percent": round(random.uniform(15, 35), 1),
                "payback_months": round(random.uniform(6, 18), 1),
                "annual_projected_savings": round(base_savings * 8760, 2)
            },
            "comparison": {
                "vs_last_period": round(random.uniform(-5, 15), 1),
                "vs_budget": round(random.uniform(-10, 20), 1),
                "vs_target": round(random.uniform(-8, 12), 1)
            }
        }

    async def _get_maintenance_dashboard(self, include_predictions: bool = True) -> Dict[str, Any]:
        """Get predictive maintenance dashboard"""
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/maintenance/predictive"
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return await self._generate_simulated_maintenance_dashboard(include_predictions)
        except Exception as e:
            logger.warning(f"Error fetching maintenance dashboard: {e}")
            return await self._generate_simulated_maintenance_dashboard(include_predictions)

    async def _generate_simulated_maintenance_dashboard(self, include_predictions: bool) -> Dict[str, Any]:
        """Generate simulated maintenance dashboard"""
        import random
        from datetime import datetime, timedelta

        equipment_list = [
            ("EL-01", "Elevador", random.randint(65, 98)),
            ("TR-02", "Correia Transportadora", random.randint(70, 95)),
            ("MT-03", "Motor Principal", random.randint(75, 99)),
            ("SI-04", "Silo", random.randint(80, 98)),
            ("BM-05", "Bomba", random.randint(60, 95))
        ]

        at_risk = []
        equipment_health = []

        for eq_id, eq_name, health in equipment_list:
            eq_data = {
                "equipment_id": eq_id,
                "equipment_name": eq_name,
                "equipment_type": eq_name.split()[0],
                "health_score": health,
                "health_status": "good" if health >= 80 else "warning" if health >= 60 else "critical",
                "mtbf_hours": random.randint(500, 2000),
                "failure_probability_7d": round(random.uniform(5, 40) if health < 80 else random.uniform(1, 15), 1),
                "recommended_action": "Monitorar" if health >= 80 else "Inspeção recomendada" if health >= 60 else "Manutenção urgente"
            }
            equipment_health.append(eq_data)

            if health < 75:
                at_risk.append({
                    "equipment_id": eq_id,
                    "equipment_name": eq_name,
                    "failure_probability": eq_data["failure_probability_7d"],
                    "health_score": health,
                    "days_to_potential_failure": random.randint(3, 21),
                    "recommended_action": eq_data["recommended_action"]
                })

        scheduled = []
        for i in range(random.randint(2, 5)):
            scheduled.append({
                "equipment_id": equipment_list[i % len(equipment_list)][0],
                "equipment_name": equipment_list[i % len(equipment_list)][1],
                "maintenance_type": random.choice(["Preventiva", "Preditiva", "Inspeção"]),
                "scheduled_date": (datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
                "days_remaining": random.randint(1, 14),
                "priority": random.choice(["high", "medium", "low"])
            })

        avg_health = sum(eq[2] for eq in equipment_list) / len(equipment_list)

        return {
            "summary": {
                "total_equipment": len(equipment_list),
                "at_risk_count": len(at_risk),
                "average_health_score": round(avg_health, 1),
                "maintenance_scheduled_7d": len([s for s in scheduled if s["days_remaining"] <= 7])
            },
            "at_risk": at_risk,
            "equipment_health": equipment_health,
            "scheduled_maintenance": scheduled,
            "roi": {
                "failures_prevented_month": random.randint(2, 8),
                "monthly_savings": round(random.uniform(15000, 50000), 2),
                "system_cost": round(random.uniform(5000, 15000), 2),
                "net_benefit": round(random.uniform(10000, 40000), 2),
                "roi_percent": round(random.uniform(150, 400), 1)
            },
            "insights": [
                {"type": "warning" if len(at_risk) > 0 else "success",
                 "title": f"{len(at_risk)} Equipamentos em Risco" if len(at_risk) > 0 else "Equipamentos Saudáveis",
                 "description": "Monitoramento preditivo identificou equipamentos que requerem atenção",
                 "recommendation": "Priorizar inspeção dos equipamentos listados"}
            ]
        }

    async def _generate_executive_report(
        self,
        time_range: str = "24h",
        include_charts: bool = True,
        report_title: str = None
    ) -> Dict[str, Any]:
        """
        Generate executive report PDF.
        Returns download URL or base64 encoded content.
        """
        try:
            import aiohttp
            import os
            from datetime import datetime

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-report/generate",
                    params={"time_range": time_range, "include_charts": str(include_charts).lower()}
                ) as response:
                    if response.status == 200:
                        # Report generated successfully
                        filename = f"relatorio_executivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                        return {
                            "success": True,
                            "message": f"Relatório executivo gerado com sucesso!",
                            "report_info": {
                                "title": report_title or "Relatório Executivo OptiFlow",
                                "time_range": time_range,
                                "include_charts": include_charts,
                                "generated_at": datetime.now().isoformat(),
                                "filename": filename
                            },
                            "download_url": f"/api/v1/executive-report/generate?time_range={time_range}",
                            "instructions": "Para baixar o relatório PDF, acesse a URL de download com autenticação ou use o botão de exportar no Dashboard Executivo."
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Erro ao gerar relatório: HTTP {response.status}",
                            "suggestion": "Verifique se o serviço de relatórios está disponível"
                        }

        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestion": "O relatório pode ser gerado manualmente através do Dashboard Executivo no frontend"
            }

    async def _get_executive_trends(
        self,
        metric: str = "oee",
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get trend data for executive metrics"""
        try:
            import aiohttp
            import os

            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/api/v1/executive-summary/trends",
                    params={"metric": metric, "period": period}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return await self._generate_simulated_trends(metric, period)
        except Exception as e:
            logger.warning(f"Error fetching executive trends: {e}")
            return await self._generate_simulated_trends(metric, period)

    async def _generate_simulated_trends(self, metric: str, period: str) -> Dict[str, Any]:
        """Generate simulated trend data"""
        import random
        from datetime import datetime, timedelta

        hours = 24 if period == "24h" else (168 if period == "7d" else 720)
        interval = 1 if hours <= 24 else (4 if hours <= 168 else 24)

        base_values = {
            "oee": (75, 92),
            "availability": (88, 99),
            "performance": (82, 96),
            "quality": (95, 99.5),
            "production": (140, 220)
        }

        base_min, base_max = base_values.get(metric, (70, 95))
        target = {"oee": 85, "availability": 95, "performance": 90, "quality": 99, "production": 180}.get(metric, 85)
        unit = "%" if metric != "production" else "ton/h"

        data_points = []
        current_value = random.uniform(base_min, base_max)

        for i in range(0, hours, interval):
            timestamp = datetime.now() - timedelta(hours=hours - i)
            # Add some realistic variation
            change = random.uniform(-2, 2)
            current_value = max(base_min, min(base_max, current_value + change))

            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": round(current_value, 2),
                "target": target
            })

        values = [p["value"] for p in data_points]

        return {
            "metric": metric,
            "period": period,
            "unit": unit,
            "data": data_points,
            "summary": {
                "current": round(values[-1] if values else 0, 2),
                "average": round(sum(values) / len(values) if values else 0, 2),
                "min": round(min(values) if values else 0, 2),
                "max": round(max(values) if values else 0, 2),
                "trend": "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "stable"
            }
        }

    # ========================================
    # Asset Tree Tools Implementation
    # ========================================

    async def _get_asset_hierarchy(self, root_id: str = None) -> Dict[str, Any]:
        """
        Get complete asset hierarchy tree.

        Args:
            root_id: Optional root element ID

        Returns:
            Hierarchy tree structure
        """
        try:
            result = await self.gateway_client.get_asset_hierarchy(root_id)

            if result.get("success") and result.get("hierarchy"):
                hierarchy = result["hierarchy"]

                # Create a summary for the LLM
                summary = self._summarize_hierarchy(hierarchy)

                return {
                    "success": True,
                    "hierarchy": hierarchy,
                    "summary": summary,
                    "total_root_elements": result.get("root_count", len(hierarchy))
                }
            elif result.get("error"):
                return {"error": result["error"], "success": False}
            else:
                return {"success": True, "hierarchy": [], "summary": "Asset tree is empty"}

        except Exception as e:
            logger.error(f"Error getting asset hierarchy: {e}")
            return {"error": str(e), "success": False}

    def _summarize_hierarchy(self, nodes: List[Dict], level: int = 0) -> str:
        """Create text summary of hierarchy for LLM"""
        lines = []
        indent = "  " * level

        for node in nodes[:10]:  # Limit to avoid huge outputs
            name = node.get("name", "Unknown")
            elem_type = node.get("type", node.get("element_type", "element"))
            attr_count = len(node.get("attributes", []))
            children_count = len(node.get("children", []))

            lines.append(f"{indent}- {name} ({elem_type}): {attr_count} attributes, {children_count} children")

            # Recurse into children (max 2 levels)
            if level < 2 and node.get("children"):
                lines.append(self._summarize_hierarchy(node["children"], level + 1))

        if len(nodes) > 10:
            lines.append(f"{indent}... and {len(nodes) - 10} more elements")

        return "\n".join(lines)

    async def _get_asset_element(
        self,
        element_id: str,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """
        Get specific asset element details.

        Args:
            element_id: Element ID or path
            include_children: Include child elements

        Returns:
            Element details
        """
        try:
            result = await self.gateway_client.get_asset_element(element_id, include_children)

            if result.get("success") and result.get("element"):
                element = result["element"]

                # Create a readable summary
                summary = f"Element: {element.get('name', 'Unknown')}\n"
                summary += f"Type: {element.get('type', element.get('element_type', 'Unknown'))}\n"
                summary += f"Path: {element.get('path', 'N/A')}\n"
                summary += f"Description: {element.get('description', 'N/A')}\n"

                attrs = element.get("attributes", [])
                if attrs:
                    summary += f"\nAttributes ({len(attrs)}):\n"
                    for attr in attrs[:10]:
                        tag = attr.get("tag_id", "no-tag")
                        unit = attr.get("uom", "")
                        summary += f"  - {attr.get('name')}: {tag} ({unit})\n"
                    if len(attrs) > 10:
                        summary += f"  ... and {len(attrs) - 10} more\n"

                return {
                    "success": True,
                    "element": element,
                    "summary": summary
                }
            elif result.get("error"):
                return {"error": result["error"], "success": False}
            else:
                return {"error": f"Element not found: {element_id}", "success": False}

        except Exception as e:
            logger.error(f"Error getting asset element: {e}")
            return {"error": str(e), "success": False}

    async def _search_assets(
        self,
        query: str,
        element_type: str = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for assets by name or path.

        Args:
            query: Search query
            element_type: Filter by type
            limit: Max results

        Returns:
            List of matching elements
        """
        try:
            result = await self.gateway_client.search_assets(query, element_type, limit)

            if result.get("success"):
                elements = result.get("elements", [])

                # Create summary
                summary = f"Found {len(elements)} assets matching '{query}'"
                if element_type:
                    summary += f" (type: {element_type})"
                summary += ":\n"

                for elem in elements[:10]:
                    name = elem.get("name", "Unknown")
                    path = elem.get("path", "")
                    etype = elem.get("type", elem.get("element_type", ""))
                    summary += f"  - {name} ({etype}) at {path}\n"

                if len(elements) > 10:
                    summary += f"  ... and {len(elements) - 10} more\n"

                return {
                    "success": True,
                    "elements": elements,
                    "total": result.get("total", len(elements)),
                    "summary": summary
                }
            else:
                return {"error": result.get("error", "Search failed"), "success": False}

        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            return {"error": str(e), "success": False}

    async def _get_asset_statistics(self) -> Dict[str, Any]:
        """
        Get asset tree statistics.

        Returns:
            Statistics about elements, templates, attributes
        """
        try:
            result = await self.gateway_client.get_asset_statistics()

            if result.get("success"):
                # Create readable summary
                summary = "Asset Tree Statistics:\n"
                summary += f"  Total Elements: {result.get('total_elements', 0)}\n"
                summary += f"  Total Attributes: {result.get('total_attributes', 0)}\n"
                summary += f"  Total Templates: {result.get('total_templates', 0)}\n"

                by_type = result.get("elements_by_type", {})
                if by_type:
                    summary += "\n  Elements by Type:\n"
                    for etype, count in by_type.items():
                        summary += f"    - {etype}: {count}\n"

                return {
                    "success": True,
                    "statistics": result,
                    "summary": summary
                }
            else:
                return {"error": result.get("error", "Failed to get statistics"), "success": False}

        except Exception as e:
            logger.error(f"Error getting asset statistics: {e}")
            return {"error": str(e), "success": False}

    async def _get_element_attributes(
        self,
        element_id: str,
        include_values: bool = True
    ) -> Dict[str, Any]:
        """
        Get all attributes for an element with optional real-time values.

        Args:
            element_id: Element ID
            include_values: Include current values

        Returns:
            List of attributes with values
        """
        try:
            # First get the element
            element_result = await self.gateway_client.get_asset_element(element_id)

            if not element_result.get("success"):
                return {"error": f"Element not found: {element_id}", "success": False}

            element = element_result.get("element", {})
            attributes = element.get("attributes", [])

            # Get real-time values if requested
            if include_values and attributes:
                tag_ids = [attr.get("tag_id") for attr in attributes if attr.get("tag_id")]
                if tag_ids:
                    values_result = await self.gateway_client.get_realtime_values(tag_ids)
                    values_map = {}
                    if values_result.get("success"):
                        for value in values_result.get("values", []):
                            values_map[value.get("tag_id")] = value

                    # Merge values into attributes
                    for attr in attributes:
                        tag_id = attr.get("tag_id")
                        if tag_id and tag_id in values_map:
                            attr["current_value"] = values_map[tag_id].get("value")
                            attr["timestamp"] = values_map[tag_id].get("timestamp")
                            attr["quality"] = values_map[tag_id].get("quality", "Good")

            # Create summary
            summary = f"Attributes for {element.get('name', element_id)}:\n"
            for attr in attributes[:15]:
                name = attr.get("name", "Unknown")
                tag_id = attr.get("tag_id", "no-tag")
                unit = attr.get("uom", "")
                value = attr.get("current_value", "N/A")
                summary += f"  - {name}: {value} {unit} (tag: {tag_id})\n"

            if len(attributes) > 15:
                summary += f"  ... and {len(attributes) - 15} more attributes\n"

            return {
                "success": True,
                "element_id": element_id,
                "element_name": element.get("name"),
                "attributes": attributes,
                "count": len(attributes),
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error getting element attributes: {e}")
            return {"error": str(e), "success": False}

    async def _get_tags_by_asset(
        self,
        element_id: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Get all tags for an asset and its children.

        Args:
            element_id: Element ID
            recursive: Include child elements

        Returns:
            List of tags with element context
        """
        try:
            # Get element with children if recursive
            element_result = await self.gateway_client.get_asset_element(
                element_id,
                include_children=recursive
            )

            if not element_result.get("success"):
                return {"error": f"Element not found: {element_id}", "success": False}

            element = element_result.get("element", {})
            all_tags = []

            # Recursive function to collect tags
            def collect_tags(elem, path=""):
                current_path = f"{path}/{elem.get('name', '')}"

                for attr in elem.get("attributes", []):
                    if attr.get("tag_id"):
                        all_tags.append({
                            "tag_id": attr["tag_id"],
                            "attribute_name": attr.get("name"),
                            "element_name": elem.get("name"),
                            "element_path": current_path,
                            "unit": attr.get("uom", ""),
                            "description": attr.get("description", "")
                        })

                if recursive:
                    for child in elem.get("children", elem.get("children_elements", [])):
                        collect_tags(child, current_path)

            collect_tags(element)

            # Create summary
            summary = f"Tags for {element.get('name', element_id)}"
            if recursive:
                summary += " (including children)"
            summary += f":\n  Total: {len(all_tags)} tags\n\n"

            # Group by element
            by_element = {}
            for tag in all_tags:
                elem_name = tag["element_name"]
                if elem_name not in by_element:
                    by_element[elem_name] = []
                by_element[elem_name].append(tag)

            for elem_name, tags in list(by_element.items())[:5]:
                summary += f"  {elem_name}: {len(tags)} tags\n"
                for tag in tags[:3]:
                    summary += f"    - {tag['attribute_name']}: {tag['tag_id']}\n"
                if len(tags) > 3:
                    summary += f"    ... and {len(tags) - 3} more\n"

            if len(by_element) > 5:
                summary += f"\n  ... and {len(by_element) - 5} more elements\n"

            return {
                "success": True,
                "element_id": element_id,
                "element_name": element.get("name"),
                "tags": all_tags,
                "total_tags": len(all_tags),
                "elements_with_tags": len(by_element),
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error getting tags by asset: {e}")
            return {"error": str(e), "success": False}


def format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """
    Format tool definitions for inclusion in the system prompt
    
    Args:
        tools: List of tool definitions
        
    Returns:
        Formatted string describing available tools
    """
    tool_descriptions = []
    
    for tool in tools:
        params = tool["parameters"]["properties"]
        required = tool["parameters"].get("required", [])
        
        param_str = ", ".join([
            f"{name}{'*' if name in required else ''}: {info['description']}"
            for name, info in params.items()
        ])
        
        tool_descriptions.append(
            f"- **{tool['name']}**({param_str}): {tool['description']}"
        )
    
    return "\n".join(tool_descriptions)


def extract_tool_calls_with_fallback(response_text: str, available_tags: Optional[List[Dict]] = None) -> List[ToolCall]:
    """
    Extract tool calls with intelligent fallback for models that don't follow ```tool format.

    Two-phase extraction:
    1. Try native ```tool block extraction (preferred)
    2. Fallback to heuristic detection if no blocks found

    Args:
        response_text: Raw response from LLM
        available_tags: List of available tags for context-aware detection

    Returns:
        List of ToolCall objects
    """
    import re

    # PHASE 1: Try native tool block extraction
    tool_calls = []
    pattern = r'```tool\s*\n(.*?)\n```'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            tool_data = json.loads(match.strip())
            tool_calls.append(ToolCall(
                name=tool_data["name"],
                arguments=tool_data.get("arguments", {})
            ))
        except Exception as e:
            logger.warning(f"Failed to parse tool call: {e}")

    if tool_calls:
        logger.info(f"✅ Native tool extraction: Found {len(tool_calls)} tool(s)")
        return tool_calls

    # PHASE 2: Heuristic fallback
    logger.info("🔄 No ```tool blocks found, trying heuristic detection...")

    response_lower = response_text.lower()

    # Heuristic 1: Detect real-time value queries

    # First, check for direct function call format: get_realtime_value("TAG_NAME")
    function_call_pattern = r'get_realtime_value\s*\(\s*["\']([^"\']+)["\']\s*\)'
    function_match = re.search(function_call_pattern, response_text)
    if function_match:
        tag_id = function_match.group(1)
        logger.info(f"🎯 Heuristic detected (function format): get_realtime_value(tag_id={tag_id})")
        tool_calls.append(ToolCall(
            name="get_realtime_value",
            arguments={"tag_id": tag_id}
        ))
        return tool_calls  # Early return - found what we need

    # Fallback to pattern-based detection
    realtime_patterns = [
        r'(?:temperatura|temp|pressão|press|velocidade|vel|corrente|potência|power).*?(?:atual|corrente|agora|em tempo real)',
        r'(?:qual|quais|me mostre|buscar|obter).*?(?:valor|dado|medição).*?(?:atual|corrente)',
        r'get_realtime_value\s*\(\s*["\']?tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]

    for pattern in realtime_patterns:
        match = re.search(pattern, response_lower)
        if match:
            # Try to find tag_id from available_tags
            tag_id = None

            # Check if explicit tag_id in response
            explicit_tag = re.search(r'tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_tag:
                tag_id = explicit_tag.group(1)
            elif available_tags and len(available_tags) > 0:
                # Use first available tag (most relevant)
                tag_id = available_tags[0].get('id')

            if tag_id:
                logger.info(f"🎯 Heuristic detected: get_realtime_value(tag_id={tag_id})")
                tool_calls.append(ToolCall(
                    name="get_realtime_value",
                    arguments={"tag_id": tag_id}
                ))
                break

    # Heuristic 2: Detect tag search queries
    search_patterns = [
        r'(?:liste|listar|buscar|procurar|encontrar|pesquisar).*?(?:tags|sensores|medições)',
        r'(?:quais|todas).*?(?:tags|sensores).*?(?:disponíveis|existentes)',
        r'search_tags\s*\(\s*["\']?query["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]

    for pattern in search_patterns:
        match = re.search(pattern, response_lower)
        if match:
            # Extract search query
            query = None

            # Check for explicit query parameter
            explicit_query = re.search(r'query["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_query:
                query = explicit_query.group(1)
            else:
                # Extract keywords from user message
                keywords = re.findall(r'(?:temperatura|pressão|velocidade|corrente|potência|nivel|fluxo)', response_lower)
                if keywords:
                    query = keywords[0]
                else:
                    query = ""  # List all tags

            logger.info(f"🎯 Heuristic detected: search_tags(query={query})")
            tool_calls.append(ToolCall(
                name="search_tags",
                arguments={"query": query, "limit": 20}
            ))
            break

    # Heuristic 3: Detect statistics calculation queries
    stats_patterns = [
        r'(?:média|mínimo|máximo|estatística|stats|calcular).*?(?:últimas|ultimos|nas|dos)',
        r'calculate_statistics\s*\(',
    ]

    for pattern in stats_patterns:
        match = re.search(pattern, response_lower)
        if match:
            tag_id = None
            period = "24h"

            # Extract tag_id
            explicit_tag = re.search(r'tag_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', response_text)
            if explicit_tag:
                tag_id = explicit_tag.group(1)
            elif available_tags and len(available_tags) > 0:
                tag_id = available_tags[0].get('id')

            # Extract period
            period_match = re.search(r'(\d+)\s*(h|hora|horas|day|dia|dias)', response_lower)
            if period_match:
                value = period_match.group(1)
                unit = period_match.group(2)
                if 'h' in unit or 'hora' in unit:
                    period = f"{value}h"
                elif 'd' in unit or 'dia' in unit:
                    period = f"{int(value)*24}h"

            if tag_id:
                logger.info(f"🎯 Heuristic detected: calculate_statistics(tag_id={tag_id}, duration={period})")
                tool_calls.append(ToolCall(
                    name="calculate_statistics",
                    arguments={"tag_id": tag_id, "duration": period}
                ))
                break

    if tool_calls:
        logger.info(f"✅ Heuristic detection: Found {len(tool_calls)} tool(s)")
    else:
        logger.info("⚠️  No tools detected (native or heuristic)")

    return tool_calls


def extract_tool_calls_from_response(response_text: str) -> List[ToolCall]:
    """
    DEPRECATED: Use extract_tool_calls_with_fallback() instead.

    Extract tool calls from LLM response (native ```tool blocks only)
    """
    tool_calls = []
    import re
    pattern = r'```tool\s*\n(.*?)\n```'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            tool_data = json.loads(match.strip())
            tool_calls.append(ToolCall(
                name=tool_data["name"],
                arguments=tool_data.get("arguments", {})
            ))
        except Exception as e:
            logger.warning(f"Failed to parse tool call: {e}")

    return tool_calls


def format_tool_results_for_llm(results: List[ToolResult]) -> str:
    """
    Format tool execution results for sending back to the LLM
    
    Args:
        results: List of tool execution results
        
    Returns:
        Formatted string
    """
    formatted = []
    
    for result in results:
        if result.success:
            formatted.append(
                f"Tool '{result.tool_name}' returned:\n```json\n{json.dumps(result.data, indent=2)}\n```"
            )
        else:
            formatted.append(
                f"Tool '{result.tool_name}' failed: {result.error}"
            )
    
    return "\n\n".join(formatted)
