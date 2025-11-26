"""
Alarms API Routes for Gateway Edge
==================================

Provides REST API endpoints for alarm management:
- Get active alarms from Gateway
- Get alarm statistics
- Get alarm history (local buffer)

Note: Gateway is the ONLY source of alarms in the architecture.
Backend consumes alarm events from Kafka and stores them.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.logger import logger

router = APIRouter()


def get_alarm_evaluator():
    """Get alarm evaluator from global state"""
    from app.services.alarm_evaluator import get_alarm_evaluator
    return get_alarm_evaluator()


@router.get("/active")
async def get_active_alarms():
    """
    Get all currently active alarms from Gateway

    These are alarms that have been triggered but not yet cleared.

    **Returns**:
    ```json
    {
      "count": 3,
      "gateway_id": "gateway-001",
      "alarms": [
        {
          "event_id": "uuid",
          "tag_id": "tag_123",
          "tag_name": "SILO1_TEMP",
          "alarm_type": "high_limit",
          "severity": "high",
          "state": "active",
          "message": "Temperature high alarm",
          "trigger_value": 85.5,
          "threshold_value": 80.0,
          "timestamp": "2025-01-19T10:30:00Z",
          "gateway_id": "gateway-001",
          "adapter_id": "opcua-001"
        }
      ],
      "timestamp": "2025-01-19T10:35:00Z"
    }
    ```
    """
    try:
        evaluator = get_alarm_evaluator()
        active_alarms = evaluator.get_active_alarms()

        return {
            "count": len(active_alarms),
            "gateway_id": evaluator.gateway_id,
            "alarms": active_alarms,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Error getting active alarms: {e}")
        raise HTTPException(500, f"Error getting active alarms: {str(e)}")


@router.get("/statistics")
async def get_alarm_statistics():
    """
    Get alarm evaluation statistics

    **Returns**:
    ```json
    {
      "gateway_id": "gateway-001",
      "evaluations": 1500,
      "alarms_triggered": 25,
      "alarms_cleared": 22,
      "active_count": 3,
      "last_evaluation": "2025-01-19T10:35:00Z"
    }
    ```
    """
    try:
        evaluator = get_alarm_evaluator()
        stats = evaluator.get_statistics()

        return {
            "gateway_id": evaluator.gateway_id,
            **stats
        }

    except Exception as e:
        logger.error(f"Error getting alarm statistics: {e}")
        raise HTTPException(500, f"Error getting alarm statistics: {str(e)}")


@router.get("/config")
async def get_alarm_configuration():
    """
    Get alarm configuration for all managed tags

    Shows which tags have alarms configured and their thresholds.

    **Returns**:
    ```json
    {
      "count": 5,
      "tags_with_alarms": [
        {
          "tag_id": "tag_123",
          "tag_name": "SILO1_TEMP",
          "alarm": {
            "enabled": true,
            "hi_hi": 95.0,
            "hi": 80.0,
            "lo": 20.0,
            "lo_lo": 10.0,
            "deadband": 2.0
          },
          "advanced_alarms": []
        }
      ]
    }
    ```
    """
    try:
        evaluator = get_alarm_evaluator()
        tag_configs = evaluator.load_tag_configs()

        tags_with_alarms = []
        for tag_id, tag_config in tag_configs.items():
            alarm_config = tag_config.get('alarm')
            advanced_alarms = tag_config.get('advanced_alarms', [])

            # Only include tags that have alarms configured
            has_basic = alarm_config and alarm_config.get('enabled')
            has_advanced = any(a.get('enabled') for a in advanced_alarms)

            if has_basic or has_advanced:
                tags_with_alarms.append({
                    "tag_id": tag_id,
                    "tag_name": tag_config.get('tag_name'),
                    "adapter_id": tag_config.get('adapter_id'),
                    "alarm": alarm_config,
                    "advanced_alarms": advanced_alarms
                })

        return {
            "count": len(tags_with_alarms),
            "total_tags": len(tag_configs),
            "tags_with_alarms": tags_with_alarms
        }

    except Exception as e:
        logger.error(f"Error getting alarm configuration: {e}")
        raise HTTPException(500, f"Error getting alarm configuration: {str(e)}")


@router.get("/summary")
async def get_alarm_summary():
    """
    Get a quick summary of alarm status

    Useful for dashboard widgets.

    **Returns**:
    ```json
    {
      "active": 3,
      "by_severity": {
        "critical": 1,
        "high": 2,
        "medium": 0,
        "low": 0
      },
      "by_type": {
        "high_limit": 2,
        "low_limit": 1
      },
      "total_triggered_today": 15,
      "total_cleared_today": 12
    }
    ```
    """
    try:
        evaluator = get_alarm_evaluator()
        active_alarms = evaluator.get_active_alarms()
        stats = evaluator.get_statistics()

        # Count by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}

        for alarm in active_alarms:
            severity = alarm.get('severity', 'medium')
            alarm_type = alarm.get('alarm_type', 'unknown')

            if severity in by_severity:
                by_severity[severity] += 1

            by_type[alarm_type] = by_type.get(alarm_type, 0) + 1

        return {
            "active": len(active_alarms),
            "by_severity": by_severity,
            "by_type": by_type,
            "total_triggered": stats['alarms_triggered'],
            "total_cleared": stats['alarms_cleared'],
            "evaluations": stats['evaluations'],
            "last_evaluation": stats['last_evaluation']
        }

    except Exception as e:
        logger.error(f"Error getting alarm summary: {e}")
        raise HTTPException(500, f"Error getting alarm summary: {str(e)}")


@router.post("/test/{tag_id}")
async def test_alarm_evaluation(tag_id: str, test_value: float = Query(...)):
    """
    Test alarm evaluation for a specific tag (without triggering real alarm)

    Useful for testing alarm configuration.

    **Query Parameters**:
    - `test_value`: The value to test against alarm thresholds

    **Returns**:
    ```json
    {
      "tag_id": "tag_123",
      "test_value": 85.5,
      "would_trigger": true,
      "alarm_type": "high_limit",
      "threshold": 80.0,
      "message": "SILO1_TEMP: High alarm - Value 85.5 > 80.0"
    }
    ```
    """
    try:
        evaluator = get_alarm_evaluator()
        tag_configs = evaluator.load_tag_configs()

        if tag_id not in tag_configs:
            raise HTTPException(404, f"Tag {tag_id} not found in managed tags")

        tag_config = tag_configs[tag_id]
        alarm_config = tag_config.get('alarm', {})

        if not alarm_config.get('enabled'):
            return {
                "tag_id": tag_id,
                "test_value": test_value,
                "would_trigger": False,
                "reason": "Alarm not enabled for this tag"
            }

        # Check thresholds
        results = []

        if alarm_config.get('hi_hi') and test_value > alarm_config['hi_hi']:
            results.append({
                "alarm_type": "high_high_limit",
                "severity": alarm_config.get('hi_hi_severity', 'critical'),
                "threshold": alarm_config['hi_hi']
            })

        if alarm_config.get('hi') and test_value > alarm_config['hi']:
            results.append({
                "alarm_type": "high_limit",
                "severity": alarm_config.get('hi_severity', 'high'),
                "threshold": alarm_config['hi']
            })

        if alarm_config.get('lo') and test_value < alarm_config['lo']:
            results.append({
                "alarm_type": "low_limit",
                "severity": alarm_config.get('lo_severity', 'high'),
                "threshold": alarm_config['lo']
            })

        if alarm_config.get('lo_lo') and test_value < alarm_config['lo_lo']:
            results.append({
                "alarm_type": "low_low_limit",
                "severity": alarm_config.get('lo_lo_severity', 'critical'),
                "threshold": alarm_config['lo_lo']
            })

        return {
            "tag_id": tag_id,
            "tag_name": tag_config.get('tag_name'),
            "test_value": test_value,
            "would_trigger": len(results) > 0,
            "triggered_alarms": results,
            "alarm_config": alarm_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing alarm: {e}")
        raise HTTPException(500, f"Error testing alarm: {str(e)}")
