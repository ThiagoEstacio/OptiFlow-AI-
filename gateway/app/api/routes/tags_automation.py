"""
Advanced Tag Automation API - Formulas, Alarms, Events, Actions
Provides enterprise automation features for tags
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.logger import logger
from app.models.tag_config import (
    FormulaConfig, AdvancedAlarmConfig, EventTrigger, AutomatedAction,
    DataValidation, AlarmType, EventType, ActionType, ValidationRule,
    TagPriority
)
from app.services.tag_manager import get_tag_manager


router = APIRouter()


# ==================== FORMULAS ====================

class FormulaCreateRequest(BaseModel):
    """Create formula for calculated tag"""
    tag_id: str
    expression: str
    input_tags: List[str]
    update_interval_ms: int = 1000
    cache_inputs: bool = True
    on_error_value: Optional[Any] = None


class FormulaTestRequest(BaseModel):
    """Test formula with sample values"""
    expression: str
    sample_values: Dict[str, Any]  # {"tag_name": value}


@router.post("/formulas/test")
async def test_formula(request: FormulaTestRequest):
    """
    Test formula expression with sample values

    **Example**:
    ```json
    {
      "expression": "tags['TEMP_C'] * 1.8 + 32",
      "sample_values": {"TEMP_C": 100}
    }
    ```

    **Returns**: Calculated value and any errors
    """
    try:
        # Create safe evaluation context
        import math
        tags = request.sample_values

        safe_dict = {
            'tags': tags,
            'math': math,
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
            'sum': sum,
            'len': len
        }

        # Evaluate expression
        result = eval(request.expression, {"__builtins__": {}}, safe_dict)

        return {
            "success": True,
            "result": result,
            "expression": request.expression,
            "inputs": request.sample_values
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "expression": request.expression,
            "inputs": request.sample_values
        }


@router.post("/tags/{tag_id}/formula")
async def create_tag_formula(tag_id: str, request: FormulaCreateRequest):
    """
    Add calculated formula to tag

    **Formula Syntax**:
    - Access other tags: `tags['TAG_NAME']`
    - Math operations: `+`, `-`, `*`, `/`, `**`, `%`
    - Math functions: `math.sqrt()`, `math.log()`, `math.sin()`, etc
    - Built-in functions: `abs()`, `min()`, `max()`, `round()`

    **Examples**:
    - Temperature conversion: `tags['TEMP_C'] * 1.8 + 32`
    - Mass flow: `tags['VOLUME_FLOW'] * tags['DENSITY']`
    - Power: `tags['VOLTAGE'] * tags['CURRENT'] * math.sqrt(3)`
    - Average: `(tags['SENSOR_1'] + tags['SENSOR_2']) / 2`
    """
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Create formula config
    formula = FormulaConfig(
        enabled=True,
        expression=request.expression,
        input_tags=request.input_tags,
        update_interval_ms=request.update_interval_ms,
        cache_inputs=request.cache_inputs,
        on_error_value=request.on_error_value
    )

    # Update tag
    tag.formula = formula
    await tm.update_tag(tag_id, {"formula": formula})

    logger.info(f"Formula added to tag {tag_id}: {request.expression}")

    return {
        "success": True,
        "tag_id": tag_id,
        "formula": formula.dict()
    }


@router.get("/formulas/examples")
async def get_formula_examples():
    """Get formula examples for common calculations"""
    return {
        "temperature_conversion": {
            "description": "Convert Celsius to Fahrenheit",
            "expression": "tags['TEMP_C'] * 1.8 + 32",
            "input_tags": ["TEMP_C"]
        },
        "mass_flow": {
            "description": "Calculate mass flow from volume flow and density",
            "expression": "tags['VOLUME_FLOW'] * tags['DENSITY']",
            "input_tags": ["VOLUME_FLOW", "DENSITY"]
        },
        "power_3phase": {
            "description": "3-phase power calculation",
            "expression": "tags['VOLTAGE'] * tags['CURRENT'] * math.sqrt(3) * tags['POWER_FACTOR']",
            "input_tags": ["VOLTAGE", "CURRENT", "POWER_FACTOR"]
        },
        "efficiency": {
            "description": "Equipment efficiency percentage",
            "expression": "(tags['OUTPUT_POWER'] / tags['INPUT_POWER']) * 100",
            "input_tags": ["OUTPUT_POWER", "INPUT_POWER"]
        },
        "average_sensors": {
            "description": "Average of multiple sensors",
            "expression": "(tags['SENSOR_1'] + tags['SENSOR_2'] + tags['SENSOR_3']) / 3",
            "input_tags": ["SENSOR_1", "SENSOR_2", "SENSOR_3"]
        },
        "flow_from_dp": {
            "description": "Flow from differential pressure (square root)",
            "expression": "tags['K_FACTOR'] * math.sqrt(tags['DIFF_PRESSURE'])",
            "input_tags": ["K_FACTOR", "DIFF_PRESSURE"]
        },
        "specific_energy": {
            "description": "Specific energy consumption (kWh/ton)",
            "expression": "tags['ENERGY_KWH'] / max(tags['PRODUCTION_TON'], 0.001)",
            "input_tags": ["ENERGY_KWH", "PRODUCTION_TON"]
        }
    }


# ==================== ADVANCED ALARMS ====================

class AdvancedAlarmCreateRequest(BaseModel):
    """Create advanced alarm"""
    tag_id: str
    alarm_type: AlarmType
    priority: TagPriority = TagPriority.NORMAL

    # Limit-based
    high_high_limit: Optional[float] = None
    high_limit: Optional[float] = None
    low_limit: Optional[float] = None
    low_low_limit: Optional[float] = None

    # Rate of change
    max_rate_of_change: Optional[float] = None
    rate_window_seconds: float = 60.0

    # Deviation
    setpoint_tag: Optional[str] = None
    max_deviation: Optional[float] = None
    deviation_type: str = "absolute"

    # Statistical
    rolling_window_seconds: Optional[float] = None
    std_dev_multiplier: Optional[float] = None

    # Custom
    custom_condition: Optional[str] = None

    # Behavior
    alarm_deadband: float = 0.0
    delay_seconds: float = 0.0
    message_template: Optional[str] = None


@router.post("/tags/{tag_id}/alarms/advanced")
async def create_advanced_alarm(tag_id: str, request: AdvancedAlarmCreateRequest):
    """
    Create advanced alarm condition

    **Alarm Types**:

    1. **LIMIT** - Traditional high/low limits
       - `high_high_limit`, `high_limit`, `low_limit`, `low_low_limit`

    2. **RATE_OF_CHANGE** - Detect rapid changes
       - `max_rate_of_change`: Maximum allowed change per second
       - `rate_window_seconds`: Time window for calculation

    3. **DEVIATION** - Deviation from setpoint/target
       - `setpoint_tag`: Reference tag to compare against
       - `max_deviation`: Maximum allowed deviation
       - `deviation_type`: "absolute" or "percentage"

    4. **STATISTICAL** - Statistical anomaly detection
       - `rolling_window_seconds`: Window for statistics
       - `std_dev_multiplier`: Trigger if > N standard deviations

    5. **CUSTOM_FORMULA** - Custom boolean expression
       - `custom_condition`: Python expression returning bool
       - Example: `"value > 100 and tags['PUMP_STATUS'] == 'ON'"`
    """
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Create alarm
    alarm_id = f"alarm_{uuid.uuid4().hex[:8]}"
    alarm = AdvancedAlarmConfig(
        alarm_id=alarm_id,
        alarm_type=request.alarm_type,
        enabled=True,
        priority=request.priority,
        high_high_limit=request.high_high_limit,
        high_limit=request.high_limit,
        low_limit=request.low_limit,
        low_low_limit=request.low_low_limit,
        max_rate_of_change=request.max_rate_of_change,
        rate_window_seconds=request.rate_window_seconds,
        setpoint_tag=request.setpoint_tag,
        max_deviation=request.max_deviation,
        deviation_type=request.deviation_type,
        rolling_window_seconds=request.rolling_window_seconds,
        std_dev_multiplier=request.std_dev_multiplier,
        custom_condition=request.custom_condition,
        alarm_deadband=request.alarm_deadband,
        delay_seconds=request.delay_seconds,
        message_template=request.message_template
    )

    # Add to tag
    tag.advanced_alarms.append(alarm)
    await tm.update_tag(tag_id, {"advanced_alarms": tag.advanced_alarms})

    logger.info(f"Advanced alarm {alarm_id} created for tag {tag_id}: {request.alarm_type}")

    return {
        "success": True,
        "alarm_id": alarm_id,
        "tag_id": tag_id,
        "alarm": alarm.dict()
    }


@router.get("/tags/{tag_id}/alarms")
async def list_tag_alarms(tag_id: str):
    """List all alarms for a tag"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    return {
        "tag_id": tag_id,
        "simple_alarm": tag.alarm.dict() if tag.alarm else None,
        "advanced_alarms": [a.dict() for a in tag.advanced_alarms],
        "total_alarms": len(tag.advanced_alarms) + (1 if tag.alarm and tag.alarm.enabled else 0)
    }


@router.delete("/tags/{tag_id}/alarms/{alarm_id}")
async def delete_alarm(tag_id: str, alarm_id: str):
    """Delete an advanced alarm"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Find and remove alarm
    tag.advanced_alarms = [a for a in tag.advanced_alarms if a.alarm_id != alarm_id]
    await tm.update_tag(tag_id, {"advanced_alarms": tag.advanced_alarms})

    return {
        "success": True,
        "tag_id": tag_id,
        "alarm_id": alarm_id,
        "message": "Alarm deleted"
    }


# ==================== EVENT TRIGGERS ====================

class EventTriggerCreateRequest(BaseModel):
    """Create event trigger"""
    tag_id: str
    event_type: EventType
    condition: Optional[str] = None
    min_interval_seconds: float = 0.0


@router.post("/tags/{tag_id}/events")
async def create_event_trigger(tag_id: str, request: EventTriggerCreateRequest):
    """
    Create event trigger

    **Event Types**:
    - `VALUE_CHANGE` - When value changes
    - `QUALITY_CHANGE` - When quality changes
    - `ALARM_ACTIVATED` - When alarm activates
    - `ALARM_CLEARED` - When alarm clears
    - `THRESHOLD_CROSSED` - When crossing threshold
    - `FORMULA_ERROR` - When formula fails
    - `COMMUNICATION_LOST` - Connection lost
    - `COMMUNICATION_RESTORED` - Connection restored

    **Condition Examples**:
    - `"value > 100"` - Only trigger if value > 100
    - `"value > old_value"` - Only trigger on increase
    - `"quality == 'Bad'"` - Only trigger if quality bad
    """
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Create trigger
    trigger_id = f"trigger_{uuid.uuid4().hex[:8]}"
    trigger = EventTrigger(
        trigger_id=trigger_id,
        event_type=request.event_type,
        enabled=True,
        condition=request.condition,
        min_interval_seconds=request.min_interval_seconds
    )

    # Add to tag
    tag.event_triggers.append(trigger)
    await tm.update_tag(tag_id, {"event_triggers": tag.event_triggers})

    logger.info(f"Event trigger {trigger_id} created for tag {tag_id}: {request.event_type}")

    return {
        "success": True,
        "trigger_id": trigger_id,
        "tag_id": tag_id,
        "trigger": trigger.dict()
    }


@router.get("/tags/{tag_id}/events")
async def list_tag_events(tag_id: str):
    """List all event triggers for a tag"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    return {
        "tag_id": tag_id,
        "event_triggers": [t.dict() for t in tag.event_triggers],
        "total_triggers": len(tag.event_triggers)
    }


# ==================== AUTOMATED ACTIONS ====================

class ActionCreateRequest(BaseModel):
    """Create automated action"""
    tag_id: str
    action_type: ActionType

    # Webhook
    webhook_url: Optional[str] = None
    webhook_method: str = "POST"
    webhook_body_template: Optional[str] = None

    # Email
    email_to: List[str] = []
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None

    # MQTT
    mqtt_topic: Optional[str] = None
    mqtt_payload_template: Optional[str] = None

    # Script (read-only execution)
    script_code: Optional[str] = None

    # Log
    log_level: str = "INFO"
    log_message_template: Optional[str] = None

    # Dashboard notification
    notification_title: Optional[str] = None
    notification_message: Optional[str] = None
    notification_severity: str = "info"


@router.post("/tags/{tag_id}/actions")
async def create_automated_action(tag_id: str, request: ActionCreateRequest):
    """
    Create automated action

    **Action Types** (READ-ONLY Gateway - No tag writing):

    1. **WEBHOOK** - HTTP request
       - `webhook_url`: Target URL
       - `webhook_method`: GET/POST/PUT
       - `webhook_body_template`: JSON template with variables

    2. **EMAIL** - Send email notification
       - `email_to`: Recipient list
       - `email_subject_template`: Subject with variables
       - `email_body_template`: Body with variables

    3. **MQTT_PUBLISH** - Publish to MQTT topic
       - `mqtt_topic`: Topic to publish
       - `mqtt_payload_template`: Payload template
       - Note: For notifying external systems only

    4. **EXECUTE_SCRIPT** - Run Python code (read-only context)
       - `script_code`: Python code to execute
       - Note: Scripts cannot write to tags (read-only gateway)

    5. **LOG_MESSAGE** - Write to application log
       - `log_level`: DEBUG/INFO/WARNING/ERROR
       - `log_message_template`: Message template

    6. **DASHBOARD_NOTIFICATION** - UI notification
       - `notification_title`: Notification title
       - `notification_message`: Message
       - `notification_severity`: info/warning/error

    7. **SMS** - Send SMS notification
       - `sms_to`: Phone number list
       - `sms_message_template`: Message template

    **Template Variables**:
    - `{value}` - Current value
    - `{tag_name}` - Tag name
    - `{quality}` - Quality code
    - `{timestamp}` - Timestamp
    - `{alarm_level}` - Alarm level if applicable
    """
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Create action
    action_id = f"action_{uuid.uuid4().hex[:8]}"
    action = AutomatedAction(
        action_id=action_id,
        action_type=request.action_type,
        enabled=True,
        webhook_url=request.webhook_url,
        webhook_method=request.webhook_method,
        webhook_body_template=request.webhook_body_template,
        email_to=request.email_to,
        email_subject_template=request.email_subject_template,
        email_body_template=request.email_body_template,
        mqtt_topic=request.mqtt_topic,
        mqtt_payload_template=request.mqtt_payload_template,
        script_code=request.script_code,
        log_level=request.log_level,
        log_message_template=request.log_message_template,
        notification_title=request.notification_title,
        notification_message=request.notification_message,
        notification_severity=request.notification_severity
    )

    # Add to tag
    tag.actions.append(action)
    await tm.update_tag(tag_id, {"actions": tag.actions})

    logger.info(f"Automated action {action_id} created for tag {tag_id}: {request.action_type}")

    return {
        "success": True,
        "action_id": action_id,
        "tag_id": tag_id,
        "action": action.dict()
    }


@router.get("/tags/{tag_id}/actions")
async def list_tag_actions(tag_id: str):
    """List all automated actions for a tag"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    return {
        "tag_id": tag_id,
        "actions": [a.dict() for a in tag.actions],
        "total_actions": len(tag.actions)
    }


# ==================== LINK TRIGGERS TO ACTIONS ====================

@router.post("/tags/{tag_id}/events/{trigger_id}/link-action/{action_id}")
async def link_action_to_trigger(tag_id: str, trigger_id: str, action_id: str):
    """Link an action to an event trigger"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Find trigger
    trigger = next((t for t in tag.event_triggers if t.trigger_id == trigger_id), None)
    if not trigger:
        raise HTTPException(404, f"Trigger {trigger_id} not found")

    # Verify action exists
    action = next((a for a in tag.actions if a.action_id == action_id), None)
    if not action:
        raise HTTPException(404, f"Action {action_id} not found")

    # Link
    if action_id not in trigger.action_ids:
        trigger.action_ids.append(action_id)
        await tm.update_tag(tag_id, {"event_triggers": tag.event_triggers})

    return {
        "success": True,
        "trigger_id": trigger_id,
        "action_id": action_id,
        "message": "Action linked to trigger"
    }


@router.post("/tags/{tag_id}/alarms/{alarm_id}/link-action/{action_id}")
async def link_action_to_alarm(tag_id: str, alarm_id: str, action_id: str):
    """Link an action to an alarm"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Find alarm
    alarm = next((a for a in tag.advanced_alarms if a.alarm_id == alarm_id), None)
    if not alarm:
        raise HTTPException(404, f"Alarm {alarm_id} not found")

    # Verify action exists
    action = next((a for a in tag.actions if a.action_id == action_id), None)
    if not action:
        raise HTTPException(404, f"Action {action_id} not found")

    # Link
    if action_id not in alarm.action_ids:
        alarm.action_ids.append(action_id)
        await tm.update_tag(tag_id, {"advanced_alarms": tag.advanced_alarms})

    return {
        "success": True,
        "alarm_id": alarm_id,
        "action_id": action_id,
        "message": "Action linked to alarm"
    }


# ==================== DATA VALIDATION ====================

class ValidationCreateRequest(BaseModel):
    """Create data validation rule"""
    tag_id: str
    rule: ValidationRule
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: List[Any] = []
    regex_pattern: Optional[str] = None
    custom_function: Optional[str] = None
    reject_invalid: bool = False


@router.post("/tags/{tag_id}/validation")
async def create_validation_rule(tag_id: str, request: ValidationCreateRequest):
    """
    Create data validation rule

    **Validation Types**:

    1. **RANGE** - Value within min/max
       - `min_value`: Minimum allowed
       - `max_value`: Maximum allowed

    2. **ENUM** - Value in allowed list
       - `allowed_values`: List of valid values

    3. **REGEX** - String matches pattern
       - `regex_pattern`: Regex pattern

    4. **CUSTOM_FUNCTION** - Custom validation
       - `custom_function`: Python function returning bool

    **Behavior**:
    - `reject_invalid`: If True, reject invalid values
    - If False, mark quality as Uncertain
    """
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)

    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    # Create validation
    validation = DataValidation(
        enabled=True,
        rule=request.rule,
        min_value=request.min_value,
        max_value=request.max_value,
        allowed_values=request.allowed_values,
        regex_pattern=request.regex_pattern,
        custom_function=request.custom_function,
        reject_invalid=request.reject_invalid
    )

    # Update tag
    tag.validation = validation
    await tm.update_tag(tag_id, {"validation": validation})

    logger.info(f"Validation rule created for tag {tag_id}: {request.rule}")

    return {
        "success": True,
        "tag_id": tag_id,
        "validation": validation.dict()
    }


# ==================== AUTOMATION STATISTICS ====================

@router.get("/automation/statistics")
async def get_automation_statistics():
    """Get automation statistics across all tags"""
    tm = get_tag_manager()

    total_formulas = 0
    total_alarms = 0
    total_triggers = 0
    total_actions = 0
    total_validations = 0

    for tag in tm.tags.values():
        if tag.formula and tag.formula.enabled:
            total_formulas += 1
        if tag.alarm and tag.alarm.enabled:
            total_alarms += 1
        total_alarms += len([a for a in tag.advanced_alarms if a.enabled])
        total_triggers += len([t for t in tag.event_triggers if t.enabled])
        total_actions += len([a for a in tag.actions if a.enabled])
        if tag.validation and tag.validation.enabled:
            total_validations += 1

    return {
        "total_tags": len(tm.tags),
        "automation": {
            "formulas": total_formulas,
            "alarms": total_alarms,
            "event_triggers": total_triggers,
            "automated_actions": total_actions,
            "validation_rules": total_validations
        },
        "coverage": {
            "tags_with_formulas": f"{(total_formulas/max(len(tm.tags), 1))*100:.1f}%",
            "tags_with_alarms": f"{(total_alarms/max(len(tm.tags), 1))*100:.1f}%",
            "tags_with_automation": f"{((total_formulas + total_alarms + total_triggers)/max(len(tm.tags), 1)/3)*100:.1f}%"
        }
    }
