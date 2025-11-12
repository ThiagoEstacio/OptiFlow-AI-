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
        """Search for tags"""
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
        Get list of all available tags in the system
        """
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
            import httpx

            # Call the alarms API endpoint
            params = {"limit": limit}
            if severity:
                params["severity"] = severity

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/alarms/active",
                    params=params,
                    timeout=10.0
                )

                if response.status_code == 200:
                    alarms_data = response.json()

                    return {
                        "total_alarms": len(alarms_data),
                        "alarms": [
                            {
                                "alarm_id": alarm.get("id"),
                                "alarm_name": alarm.get("alarm_name"),
                                "severity": alarm.get("severity"),
                                "tag_id": str(alarm.get("tag_id")),
                                "trigger_value": alarm.get("trigger_value"),
                                "trigger_timestamp": alarm.get("trigger_timestamp"),
                                "state": alarm.get("state"),
                                "description": alarm.get("description"),
                                "alarm_type": alarm.get("alarm_type")
                            }
                            for alarm in alarms_data
                        ],
                        "filter_applied": f"severity={severity}" if severity else "all severities"
                    }
                else:
                    return {"error": f"API returned status {response.status_code}", "alarms": []}

        except Exception as e:
            logger.error(f"Error getting active alarms: {e}")
            return {"error": str(e), "alarms": []}


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


def extract_tool_calls_from_response(response_text: str) -> List[ToolCall]:
    """
    Extract tool calls from LLM response
    
    The LLM should format tool calls as:
    ```tool
    {
      "name": "get_realtime_value",
      "arguments": {"tag_id": "temp_01"}
    }
    ```
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    # Look for ```tool blocks in the response
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
