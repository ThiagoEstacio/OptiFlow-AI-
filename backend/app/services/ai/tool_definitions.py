"""
Tool Definitions for AI Agent
=============================

JSON Schema definitions for all tools available to the LLM.
Each tool has:
- name: Tool identifier
- description: When to use this tool
- parameters: JSON Schema for arguments
"""

from typing import List, Dict, Any

# Define available tools for the LLM
AVAILABLE_TOOLS: List[Dict[str, Any]] = [
    # ========================================
    # CORE DATA ACCESS TOOLS
    # ========================================
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
    # ========================================
    # ANALYSIS & COMPARISON TOOLS
    # ========================================
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
    # OEE & PRODUCTION TOOLS
    # ========================================
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
    # ========================================
    # ALARM TOOLS
    # ========================================
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
    },
    # ========================================
    # DASHBOARD MANAGEMENT - Criação e Edição
    # ========================================
    {
        "name": "create_dashboard",
        "description": "Create a new custom dashboard with optional widgets. Use when user asks to create, build, or make a new dashboard. Returns the created dashboard ID and URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Dashboard name (required)"
                },
                "description": {
                    "type": "string",
                    "description": "Dashboard description (optional)"
                },
                "module": {
                    "type": "string",
                    "enum": ["operations", "quality", "maintenance", "energy", "executive", "custom"],
                    "description": "Dashboard module/category (default: custom)"
                },
                "is_public": {
                    "type": "boolean",
                    "description": "Make dashboard public (default: false)"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "add_widget_to_dashboard",
        "description": "Add a widget (chart, gauge, table, etc.) to an existing dashboard. Use when user asks to add a chart, graph, gauge, KPI card, or visualization to a dashboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "dashboard_id": {
                    "type": "string",
                    "description": "Dashboard ID to add widget to (required)"
                },
                "title": {
                    "type": "string",
                    "description": "Widget title (required)"
                },
                "widget_type": {
                    "type": "string",
                    "enum": ["line_chart", "bar_chart", "pie_chart", "gauge", "kpi_card", "table", "heatmap", "sparkline", "area_chart", "donut_chart", "scatter_plot", "histogram", "realtime_value", "alarm_list", "trend_chart"],
                    "description": "Type of widget (required)"
                },
                "tag_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tag IDs to display in the widget"
                },
                "position": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X position (0-11)"},
                        "y": {"type": "integer", "description": "Y position"},
                        "w": {"type": "integer", "description": "Width (1-12)"},
                        "h": {"type": "integer", "description": "Height (1-12)"}
                    },
                    "description": "Widget grid position (optional, auto-positioned if not provided)"
                }
            },
            "required": ["dashboard_id", "title", "widget_type"]
        }
    },
    {
        "name": "list_dashboards",
        "description": "List all available dashboards. Use when user asks to see existing dashboards, available dashboards, or what dashboards exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "module": {
                    "type": "string",
                    "enum": ["operations", "quality", "maintenance", "energy", "executive", "custom"],
                    "description": "Filter by module (optional)"
                }
            }
        }
    },
    {
        "name": "get_dashboard_details",
        "description": "Get details of a specific dashboard including its widgets. Use when user asks about a specific dashboard or wants to see what's in a dashboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "dashboard_id": {
                    "type": "string",
                    "description": "Dashboard ID to get details for"
                }
            },
            "required": ["dashboard_id"]
        }
    }
]


def get_tool_by_name(name: str) -> Dict[str, Any] | None:
    """Get a tool definition by name."""
    for tool in AVAILABLE_TOOLS:
        if tool["name"] == name:
            return tool
    return None


def get_tool_names() -> List[str]:
    """Get list of all tool names."""
    return [tool["name"] for tool in AVAILABLE_TOOLS]
