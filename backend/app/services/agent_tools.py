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
        """Get real-time value for a tag"""
        result = await self.data_service.get_realtime_value(tag_id)
        if not result:
            return {"error": f"Tag not found: {tag_id}"}
        return result
    
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
        """Calculate statistics for a tag"""
        return await self.data_service.calculate_statistics(tag_id, duration)
    
    async def _search_tags(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tags (max 50 results to prevent overload)"""
        # PROTECTION: Limit max results to prevent memory issues
        limit = min(limit, 50)
        return await self.data_service.search_tags(query, limit)
    
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

    async def _get_active_alarms(self, severity: str = None, limit: int = 20) -> Dict[str, Any]:
        """
        Get list of currently active alarms
        """
        try:
            # Import models directly to query database instead of HTTP call
            from sqlalchemy import select
            from app.models.alarm import AlarmEvent, AlarmDefinition, AlarmState, AlarmSeverity
            from app.db.session import get_db

            # Get alarms from database directly (more reliable than HTTP from within container)
            return_value = None
            async for session in get_db():
                try:
                    # FIX N+1 QUERY: Use selectinload to eagerly load AlarmDefinition
                    from sqlalchemy.orm import selectinload

                    # Query active alarms with their definitions
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
                        "total_alarms": len(alarm_list),
                        "alarms": alarm_list,
                        "filter_applied": f"severity={severity}" if severity else "all severities"
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
            start_time = datetime.utcnow() - time_delta

            return_value = None
            async for session in get_db():
                try:
                    # Query all alarm events in time period WITH EAGER LOADING
                    # FIX N+1 QUERY: Use selectinload to load AlarmDefinition in a single query
                    from sqlalchemy.orm import selectinload

                    stmt = select(AlarmEvent).options(
                        selectinload(AlarmEvent.definition)  # Eager load relationship
                    ).where(
                        AlarmEvent.trigger_timestamp >= start_time
                    ).order_by(AlarmEvent.trigger_timestamp.desc())

                    result = await session.execute(stmt)
                    events = result.scalars().all()

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

                    while current_time < datetime.utcnow():
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

                    return_value = {
                        "duration": duration,
                        "analysis_period": {
                            "start": start_time.isoformat(),
                            "end": datetime.utcnow().isoformat(),
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

                finally:
                    await session.close()
                    break

            return return_value

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
