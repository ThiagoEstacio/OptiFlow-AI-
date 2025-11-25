"""
Advanced Tag Configuration Models
Enterprise-grade tag configuration similar to KEPServerEX and Aveva PI
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class DataType(str, Enum):
    """Supported data types"""
    BOOLEAN = "boolean"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    DATETIME = "datetime"
    BYTE_ARRAY = "byte_array"


class QualityCode(str, Enum):
    """OPC UA Quality Codes"""
    GOOD = "Good"
    UNCERTAIN = "Uncertain"
    BAD = "Bad"
    GOOD_LOCAL_OVERRIDE = "GoodLocalOverride"
    UNCERTAIN_SENSOR_NOT_ACCURATE = "UncertainSensorNotAccurate"
    BAD_NOT_CONNECTED = "BadNotConnected"
    BAD_DEVICE_FAILURE = "BadDeviceFailure"
    BAD_SENSOR_FAILURE = "BadSensorFailure"
    BAD_OUT_OF_SERVICE = "BadOutOfService"
    BAD_WAITING_FOR_INITIAL_DATA = "BadWaitingForInitialData"


class DeadbandType(str, Enum):
    """Deadband filter types"""
    NONE = "none"
    ABSOLUTE = "absolute"  # Change must exceed absolute value
    PERCENTAGE = "percentage"  # Change must exceed % of range


class ScalingMode(str, Enum):
    """Scaling/transformation modes"""
    NONE = "none"
    LINEAR = "linear"  # y = mx + b
    SQUARE_ROOT = "square_root"  # For flow from differential pressure
    CUSTOM_EXPRESSION = "custom"  # Python expression


class HistorianMode(str, Enum):
    """Data historization modes"""
    DISABLED = "disabled"  # No historization
    ON_CHANGE = "on_change"  # Only when value changes (with deadband)
    PERIODIC = "periodic"  # Fixed interval
    ON_CHANGE_AND_PERIODIC = "both"  # Hybrid mode


class TagPriority(str, Enum):
    """Tag priority for alarming and processing"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AlarmType(str, Enum):
    """Types of alarm conditions"""
    LIMIT = "limit"  # High/Low limit violation
    RATE_OF_CHANGE = "rate_of_change"  # Value changing too fast
    DEVIATION = "deviation"  # Deviation from setpoint
    STATISTICAL = "statistical"  # Statistical anomaly (std dev, etc)
    CUSTOM_FORMULA = "custom_formula"  # Custom boolean expression


class EventType(str, Enum):
    """Types of events that can be triggered"""
    VALUE_CHANGE = "value_change"
    QUALITY_CHANGE = "quality_change"
    ALARM_ACTIVATED = "alarm_activated"
    ALARM_CLEARED = "alarm_cleared"
    THRESHOLD_CROSSED = "threshold_crossed"
    FORMULA_ERROR = "formula_error"
    COMMUNICATION_LOST = "communication_lost"
    COMMUNICATION_RESTORED = "communication_restored"


class ActionType(str, Enum):
    """Types of actions that can be executed (READ-ONLY Gateway)"""
    WEBHOOK = "webhook"  # HTTP POST to URL
    EMAIL = "email"  # Send email notification
    SMS = "sms"  # Send SMS
    MQTT_PUBLISH = "mqtt_publish"  # Publish to MQTT topic
    EXECUTE_SCRIPT = "execute_script"  # Run Python script (read-only context)
    LOG_MESSAGE = "log_message"  # Write to log file
    DASHBOARD_NOTIFICATION = "dashboard_notification"  # UI notification
    # NOTE: WRITE_TAG removed - Gateway is READ-ONLY by design for safety


class ValidationRule(str, Enum):
    """Data validation rules"""
    RANGE = "range"  # Value must be within min-max
    ENUM = "enum"  # Value must be one of allowed values
    REGEX = "regex"  # String must match regex pattern
    CUSTOM_FUNCTION = "custom_function"  # Custom validation function


class ScalingConfig(BaseModel):
    """Scaling/transformation configuration"""
    mode: ScalingMode = ScalingMode.NONE

    # Linear scaling: y = (x - raw_min) * (eng_max - eng_min) / (raw_max - raw_min) + eng_min
    raw_min: Optional[float] = None
    raw_max: Optional[float] = None
    eng_min: Optional[float] = None  # Engineering units minimum
    eng_max: Optional[float] = None  # Engineering units maximum

    # Custom expression (e.g., "x * 1.8 + 32" for C to F)
    expression: Optional[str] = None

    # Clamping
    clamp_low: Optional[float] = None
    clamp_high: Optional[float] = None


class DeadbandConfig(BaseModel):
    """Deadband filtering configuration"""
    type: DeadbandType = DeadbandType.NONE
    value: float = 0.0  # Absolute value or percentage (0-100)

    # For percentage deadband, need to know the range
    range_min: Optional[float] = None
    range_max: Optional[float] = None


class HistorianConfig(BaseModel):
    """Data historization configuration"""
    enabled: bool = True  # Store in InfluxDB
    mode: HistorianMode = HistorianMode.ON_CHANGE

    # Periodic sampling
    interval_ms: int = 1000  # For periodic or hybrid mode

    # Retention policy
    retention_days: Optional[int] = None  # None = use default

    # Compression
    compress: bool = True

    # Exception reporting (only log on deadband violation)
    exception_deadband: Optional[DeadbandConfig] = None


class DataValidation(BaseModel):
    """Data validation configuration"""
    enabled: bool = False
    rule: ValidationRule = ValidationRule.RANGE

    # Range validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # Enum validation
    allowed_values: List[Any] = Field(default_factory=list)

    # Regex validation (for strings)
    regex_pattern: Optional[str] = None

    # Custom validation function (Python code)
    custom_function: Optional[str] = None

    # Action on validation failure
    on_failure_quality: QualityCode = QualityCode.UNCERTAIN
    reject_invalid: bool = False  # If true, don't update value


class FormulaConfig(BaseModel):
    """Calculated/derived tag configuration"""
    enabled: bool = False

    # Formula expression (Python-like, with access to other tags)
    # Example: "tags['TEMP_01'] * 1.8 + 32" (C to F)
    # Example: "tags['FLOW_01'] * tags['DENSITY_01']" (mass flow)
    expression: str

    # Input tags (dependencies)
    input_tags: List[str] = Field(default_factory=list)

    # Update frequency
    update_interval_ms: int = 1000

    # Cache input values
    cache_inputs: bool = True

    # Handle errors
    on_error_value: Optional[Any] = None
    on_error_quality: QualityCode = QualityCode.BAD


class AdvancedAlarmConfig(BaseModel):
    """Advanced alarm condition"""
    alarm_id: str
    alarm_type: AlarmType
    enabled: bool = True
    priority: TagPriority = TagPriority.NORMAL

    # Limit-based alarms
    high_high_limit: Optional[float] = None
    high_limit: Optional[float] = None
    low_limit: Optional[float] = None
    low_low_limit: Optional[float] = None

    # Rate of change alarm (units per second)
    max_rate_of_change: Optional[float] = None
    rate_window_seconds: float = 60.0

    # Deviation alarm (from setpoint or target)
    setpoint_tag: Optional[str] = None  # Reference tag
    max_deviation: Optional[float] = None
    deviation_type: str = "absolute"  # "absolute" or "percentage"

    # Statistical alarm
    rolling_window_seconds: Optional[float] = None
    std_dev_multiplier: Optional[float] = None  # Trigger if > N std deviations

    # Custom formula alarm (boolean expression)
    custom_condition: Optional[str] = None  # Example: "value > 100 and tags['PUMP_STATUS'] == 'ON'"

    # Alarm behavior
    alarm_deadband: float = 0.0  # Prevent flapping
    delay_seconds: float = 0.0  # Delay before activation
    auto_acknowledge: bool = False

    # Shelving (temporary disable)
    shelved: bool = False
    shelved_until: Optional[datetime] = None

    # Messages
    message_template: Optional[str] = None  # Example: "Temperature {value}°C exceeds limit {limit}°C"

    # Linked actions
    action_ids: List[str] = Field(default_factory=list)


class AlarmConfig(BaseModel):
    """Alarm/alert configuration - Simple mode"""
    enabled: bool = False

    # Limit alarms
    high_high_limit: Optional[float] = None
    high_limit: Optional[float] = None
    low_limit: Optional[float] = None
    low_low_limit: Optional[float] = None

    # Deadband for alarm (prevent flapping)
    alarm_deadband: float = 0.0

    # Delay before triggering (seconds)
    delay_seconds: float = 0.0

    # Priority
    priority: TagPriority = TagPriority.NORMAL


class EventTrigger(BaseModel):
    """Event trigger configuration"""
    trigger_id: str
    event_type: EventType
    enabled: bool = True

    # Condition (optional filter)
    condition: Optional[str] = None  # Python boolean expression

    # Linked actions
    action_ids: List[str] = Field(default_factory=list)

    # Throttling (prevent too many triggers)
    min_interval_seconds: float = 0.0
    last_trigger_time: Optional[datetime] = None


class AutomatedAction(BaseModel):
    """Automated action configuration"""
    action_id: str
    action_type: ActionType
    enabled: bool = True

    # Webhook action
    webhook_url: Optional[str] = None
    webhook_method: str = "POST"
    webhook_headers: Dict[str, str] = Field(default_factory=dict)
    webhook_body_template: Optional[str] = None  # JSON template with {value}, {tag_name}, etc

    # Email action
    email_to: List[str] = Field(default_factory=list)
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None

    # SMS action
    sms_to: List[str] = Field(default_factory=list)
    sms_message_template: Optional[str] = None

    # MQTT action
    mqtt_topic: Optional[str] = None
    mqtt_payload_template: Optional[str] = None
    mqtt_qos: int = 0
    mqtt_retain: bool = False

    # Execute script action (READ-ONLY - no write access to tags)
    script_code: Optional[str] = None  # Python code to execute (read-only context)
    script_timeout_seconds: float = 5.0

    # Log message action
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_message_template: Optional[str] = None

    # Dashboard notification
    notification_title: Optional[str] = None
    notification_message: Optional[str] = None
    notification_severity: str = "info"  # info, warning, error, success

    # Retry logic
    retry_on_failure: bool = False
    max_retries: int = 3
    retry_delay_seconds: float = 5.0


class TagMetadata(BaseModel):
    """Tag metadata and documentation"""
    description: Optional[str] = None
    engineering_units: Optional[str] = None  # e.g., "°C", "bar", "m³/h"

    # Asset/equipment linking
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    location: Optional[str] = None

    # P&ID information
    pid_tag: Optional[str] = None

    # Custom properties
    custom_properties: Dict[str, Any] = Field(default_factory=dict)


class TagConfig(BaseModel):
    """
    Enterprise Tag Configuration
    Complete tag configuration with all enterprise features
    """
    # Basic identification
    tag_id: str  # Unique identifier
    tag_name: str  # Display name
    address: str  # Protocol-specific address (NodeId, register, etc.)
    data_type: DataType

    # Protocol information
    protocol_type: str  # opcua, modbus, mqtt, etc.
    adapter_id: str  # Which adapter owns this tag

    # Enable/disable
    enabled: bool = True

    # Access rights
    read_only: bool = True

    # Quality
    quality: QualityCode = QualityCode.GOOD

    # Data transformation
    scaling: Optional[ScalingConfig] = None
    deadband: Optional[DeadbandConfig] = None

    # Historization
    historian: HistorianConfig = Field(default_factory=HistorianConfig)

    # Alarming
    alarm: Optional[AlarmConfig] = None
    advanced_alarms: List[AdvancedAlarmConfig] = Field(default_factory=list)

    # Data validation
    validation: Optional[DataValidation] = None

    # Calculated/derived tags
    formula: Optional[FormulaConfig] = None

    # Event triggers
    event_triggers: List[EventTrigger] = Field(default_factory=list)

    # Automated actions
    actions: List[AutomatedAction] = Field(default_factory=list)

    # Metadata
    metadata: TagMetadata = Field(default_factory=TagMetadata)

    # Grouping/organization
    group_path: Optional[str] = None  # e.g., "Site1/Area2/Line3"
    tags: List[str] = Field(default_factory=list)  # User-defined tags/labels

    # Current value (runtime)
    current_value: Optional[Any] = None
    current_value_timestamp: Optional[datetime] = None
    last_good_value: Optional[Any] = None
    last_change_timestamp: Optional[datetime] = None

    # Statistics
    read_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class TagGroup(BaseModel):
    """
    Tag Group/Folder
    Hierarchical organization of tags
    """
    group_id: str
    group_name: str
    parent_group_id: Optional[str] = None
    path: str  # Full path e.g., "Root/Site1/Area2"
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)  # Tag IDs
    icon: Optional[str] = None
    color: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class TagTemplate(BaseModel):
    """
    Tag Template
    Reusable configuration for common tag types
    """
    template_id: str
    template_name: str
    description: Optional[str] = None

    # Default configuration
    data_type: DataType
    scaling: Optional[ScalingConfig] = None
    deadband: Optional[DeadbandConfig] = None
    historian: HistorianConfig = Field(default_factory=HistorianConfig)
    alarm: Optional[AlarmConfig] = None
    metadata: TagMetadata = Field(default_factory=TagMetadata)

    # Usage
    usage_count: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)


class TagBrowseResult(BaseModel):
    """Result from tag browsing/discovery"""
    tag_name: str
    address: str
    data_type: DataType
    description: Optional[str] = None
    current_value: Optional[Any] = None
    quality: QualityCode = QualityCode.GOOD


class TagBulkOperation(BaseModel):
    """Bulk operations on multiple tags"""
    tag_ids: List[str]
    operation: str  # "enable", "disable", "delete", "update_historian", etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TagImportConfig(BaseModel):
    """Configuration for tag import from file"""
    file_format: str  # "csv", "excel", "json", "kepware_json"
    adapter_id: str
    overwrite_existing: bool = False
    enable_after_import: bool = True
    apply_template: Optional[str] = None  # Template ID to apply to all


class TagExportConfig(BaseModel):
    """Configuration for tag export"""
    tag_ids: Optional[List[str]] = None  # None = export all
    file_format: str  # "csv", "excel", "json"
    include_runtime_data: bool = False
    include_statistics: bool = False


# Predefined templates for common tag types
PREDEFINED_TEMPLATES = {
    "temperature_sensor": TagTemplate(
        template_id="temp_sensor",
        template_name="Temperature Sensor",
        description="Standard temperature sensor (4-20mA, 0-100°C)",
        data_type=DataType.DOUBLE,
        scaling=ScalingConfig(
            mode=ScalingMode.LINEAR,
            raw_min=4.0,
            raw_max=20.0,
            eng_min=0.0,
            eng_max=100.0
        ),
        deadband=DeadbandConfig(
            type=DeadbandType.ABSOLUTE,
            value=0.5  # 0.5°C
        ),
        historian=HistorianConfig(
            enabled=True,
            mode=HistorianMode.ON_CHANGE,
            interval_ms=5000
        ),
        alarm=AlarmConfig(
            enabled=True,
            high_limit=80.0,
            high_high_limit=90.0,
            priority=TagPriority.HIGH
        ),
        metadata=TagMetadata(
            engineering_units="°C"
        )
    ),

    "pressure_sensor": TagTemplate(
        template_id="pressure_sensor",
        template_name="Pressure Sensor",
        description="Standard pressure sensor (4-20mA, 0-10 bar)",
        data_type=DataType.DOUBLE,
        scaling=ScalingConfig(
            mode=ScalingMode.LINEAR,
            raw_min=4.0,
            raw_max=20.0,
            eng_min=0.0,
            eng_max=10.0
        ),
        deadband=DeadbandConfig(
            type=DeadbandType.PERCENTAGE,
            value=1.0,  # 1%
            range_min=0.0,
            range_max=10.0
        ),
        historian=HistorianConfig(
            enabled=True,
            mode=HistorianMode.ON_CHANGE,
            interval_ms=5000
        ),
        metadata=TagMetadata(
            engineering_units="bar"
        )
    ),

    "flow_meter": TagTemplate(
        template_id="flow_meter",
        template_name="Flow Meter (Differential Pressure)",
        description="Flow calculated from differential pressure (square root extraction)",
        data_type=DataType.DOUBLE,
        scaling=ScalingConfig(
            mode=ScalingMode.SQUARE_ROOT,
            raw_min=0.0,
            raw_max=100.0,
            eng_min=0.0,
            eng_max=1000.0
        ),
        deadband=DeadbandConfig(
            type=DeadbandType.PERCENTAGE,
            value=2.0,  # 2%
            range_min=0.0,
            range_max=1000.0
        ),
        historian=HistorianConfig(
            enabled=True,
            mode=HistorianMode.ON_CHANGE_AND_PERIODIC,
            interval_ms=10000
        ),
        metadata=TagMetadata(
            engineering_units="m³/h"
        )
    ),

    "digital_input": TagTemplate(
        template_id="digital_input",
        template_name="Digital Input",
        description="Binary sensor or switch",
        data_type=DataType.BOOLEAN,
        historian=HistorianConfig(
            enabled=True,
            mode=HistorianMode.ON_CHANGE  # Only log state changes
        )
    ),

    "setpoint": TagTemplate(
        template_id="setpoint",
        template_name="Setpoint/Command",
        description="Writable setpoint or command value",
        data_type=DataType.DOUBLE,
        historian=HistorianConfig(
            enabled=True,
            mode=HistorianMode.ON_CHANGE  # Log all setpoint changes
        )
    )
}
