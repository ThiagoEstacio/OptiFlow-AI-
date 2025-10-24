"""
Point Validation Service

Validates point configurations to ensure data quality and consistency.
Includes validation rules for:
- Engineering limits
- Scaling parameters
- Compression settings
- Historian configuration
- Alarm settings
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from app.models.tag import Tag, TagDataType
from app.models.point_config import PointConfiguration, PointTemplate, CompressionType, HistorianType


@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity
        }


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }

    def add_error(self, field: str, message: str):
        """Add validation error"""
        self.errors.append(ValidationError(field, message, "error"))
        self.is_valid = False

    def add_warning(self, field: str, message: str):
        """Add validation warning"""
        self.warnings.append(ValidationError(field, message, "warning"))


class PointValidator:
    """
    Point validation service.

    Validates point configurations against business rules and best practices.
    """

    def validate_tag(self, tag: Tag) -> ValidationResult:
        """
        Validate a Tag configuration.

        Args:
            tag: Tag to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate basic fields
        if not tag.name or len(tag.name) < 2:
            result.add_error("name", "Tag name must be at least 2 characters")

        if not tag.address:
            result.add_error("address", "Tag address is required")

        # Validate engineering limits
        if tag.min_value is not None and tag.max_value is not None:
            if tag.min_value >= tag.max_value:
                result.add_error("min_value", "min_value must be less than max_value")

        if tag.engineering_min is not None and tag.engineering_max is not None:
            if tag.engineering_min >= tag.engineering_max:
                result.add_error("engineering_min", "engineering_min must be less than engineering_max")

        # Validate scaling
        if tag.scale == 0:
            result.add_error("scale", "Scale cannot be zero (would cause division by zero)")

        # Validate scan rate
        if tag.scan_rate_ms < 10:
            result.add_warning("scan_rate_ms", "Scan rate below 10ms may cause performance issues")
        elif tag.scan_rate_ms > 3600000:  # 1 hour
            result.add_warning("scan_rate_ms", "Scan rate above 1 hour may miss important changes")

        # Validate deadband
        if tag.deadband is not None and tag.deadband < 0:
            result.add_error("deadband", "Deadband cannot be negative")

        # Validate data type compatibility
        if tag.data_type == TagDataType.BOOLEAN:
            if tag.deadband is not None and tag.deadband > 0:
                result.add_warning("deadband", "Deadband not applicable for boolean tags")

        return result

    def validate_point_template(self, template: PointTemplate) -> ValidationResult:
        """
        Validate a PointTemplate configuration.

        Args:
            template: PointTemplate to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate basic fields
        if not template.name or len(template.name) < 2:
            result.add_error("name", "Template name must be at least 2 characters")

        # Validate engineering limits
        if template.min_value is not None and template.max_value is not None:
            if template.min_value >= template.max_value:
                result.add_error("min_value", "min_value must be less than max_value")

        if template.engineering_min is not None and template.engineering_max is not None:
            if template.engineering_min >= template.engineering_max:
                result.add_error("engineering_min", "engineering_min must be less than engineering_max")

        # Validate compression configuration
        if template.compression_enabled:
            compression_errors = self._validate_compression_config(
                template.compression_type,
                template.compression_config
            )
            result.errors.extend(compression_errors)
            if compression_errors:
                result.is_valid = False

        # Validate historian configuration
        if template.historian_enabled:
            historian_errors = self._validate_historian_config(
                template.historian_type,
                template.historian_config
            )
            result.errors.extend(historian_errors)
            if historian_errors:
                result.is_valid = False

        # Validate alarm configuration
        if template.enable_alarms:
            alarm_errors = self._validate_alarm_config(template.alarm_config)
            result.errors.extend(alarm_errors)
            if alarm_errors:
                result.is_valid = False

        return result

    def validate_point_configuration(
        self,
        config: PointConfiguration,
        tag: Optional[Tag] = None
    ) -> ValidationResult:
        """
        Validate a PointConfiguration.

        Args:
            config: PointConfiguration to validate
            tag: Associated Tag (optional, for additional validation)

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate compression configuration
        if config.compression_enabled:
            compression_errors = self._validate_compression_config(
                config.compression_type,
                config.compression_config
            )
            result.errors.extend(compression_errors)
            if compression_errors:
                result.is_valid = False

        # Validate historian configuration
        if config.historian_enabled:
            historian_errors = self._validate_historian_config(
                config.historian_type,
                config.historian_config
            )
            result.errors.extend(historian_errors)
            if historian_errors:
                result.is_valid = False

        # Validate validation rules
        if config.validation_rules:
            validation_rule_errors = self._validate_validation_rules(config.validation_rules)
            result.errors.extend(validation_rule_errors)
            if validation_rule_errors:
                result.is_valid = False

        # Cross-validate with tag if provided
        if tag:
            # Check compression compatibility with data type
            if config.compression_enabled and tag.data_type == TagDataType.BOOLEAN:
                result.add_warning(
                    "compression_enabled",
                    "Compression may not be effective for boolean data types"
                )

            # Check scan rate vs compression window
            if config.compression_type == CompressionType.BOXCAR:
                time_window = config.compression_config.get("time_window_ms", 0)
                if time_window > 0 and tag.scan_rate_ms > time_window:
                    result.add_warning(
                        "compression_config",
                        f"Scan rate ({tag.scan_rate_ms}ms) is slower than compression window ({time_window}ms)"
                    )

        return result

    def _validate_compression_config(
        self,
        compression_type: CompressionType,
        config: dict
    ) -> List[ValidationError]:
        """Validate compression configuration"""
        errors = []

        if compression_type == CompressionType.NONE:
            return errors

        elif compression_type == CompressionType.SWINGING_DOOR:
            deviation = config.get("deviation")
            if deviation is None:
                errors.append(ValidationError(
                    "compression_config.deviation",
                    "SwingingDoor requires 'deviation' parameter"
                ))
            elif deviation <= 0:
                errors.append(ValidationError(
                    "compression_config.deviation",
                    "Deviation must be positive"
                ))

            time_deadband = config.get("time_deadband_ms", 0)
            if time_deadband < 0:
                errors.append(ValidationError(
                    "compression_config.time_deadband_ms",
                    "Time deadband cannot be negative"
                ))

        elif compression_type == CompressionType.BOXCAR:
            time_window = config.get("time_window_ms")
            if time_window is None:
                errors.append(ValidationError(
                    "compression_config.time_window_ms",
                    "BoxCar requires 'time_window_ms' parameter"
                ))
            elif time_window <= 0:
                errors.append(ValidationError(
                    "compression_config.time_window_ms",
                    "Time window must be positive"
                ))

            store_method = config.get("store_method", "last")
            valid_methods = ["last", "average", "min", "max", "min_max"]
            if store_method not in valid_methods:
                errors.append(ValidationError(
                    "compression_config.store_method",
                    f"Store method must be one of: {', '.join(valid_methods)}"
                ))

        elif compression_type == CompressionType.DEADBAND:
            deadband = config.get("deadband")
            deadband_percent = config.get("deadband_percent")

            if deadband is None and deadband_percent is None:
                errors.append(ValidationError(
                    "compression_config",
                    "Deadband requires either 'deadband' or 'deadband_percent'"
                ))

            if deadband is not None and deadband < 0:
                errors.append(ValidationError(
                    "compression_config.deadband",
                    "Deadband cannot be negative"
                ))

            if deadband_percent is not None and (deadband_percent < 0 or deadband_percent > 100):
                errors.append(ValidationError(
                    "compression_config.deadband_percent",
                    "Deadband percent must be between 0 and 100"
                ))

        return errors

    def _validate_historian_config(
        self,
        historian_type: HistorianType,
        config: dict
    ) -> List[ValidationError]:
        """Validate historian configuration"""
        errors = []

        if historian_type == HistorianType.NONE:
            return errors

        # Common validation for all historian types
        retention_days = config.get("retention_days")
        if retention_days is not None:
            if retention_days < 1:
                errors.append(ValidationError(
                    "historian_config.retention_days",
                    "Retention days must be at least 1"
                ))
            elif retention_days > 3650:  # 10 years
                errors.append(ValidationError(
                    "historian_config.retention_days",
                    "Retention days exceeds maximum of 3650 (10 years)"
                ))

        # InfluxDB specific validation
        if historian_type == HistorianType.INFLUXDB:
            if not config.get("measurement"):
                errors.append(ValidationError(
                    "historian_config.measurement",
                    "InfluxDB requires 'measurement' parameter"
                ))

        return errors

    def _validate_alarm_config(self, config: dict) -> List[ValidationError]:
        """Validate alarm configuration"""
        errors = []

        # Validate alarm levels
        levels = ["high_high", "high", "low", "low_low"]
        limits = {}

        for level in levels:
            level_config = config.get(level, {})
            if level_config.get("enabled"):
                limit = level_config.get("limit")
                if limit is None:
                    errors.append(ValidationError(
                        f"alarm_config.{level}.limit",
                        f"Alarm level '{level}' is enabled but has no limit"
                    ))
                else:
                    limits[level] = limit

        # Validate alarm limit ordering
        if "high_high" in limits and "high" in limits:
            if limits["high_high"] <= limits["high"]:
                errors.append(ValidationError(
                    "alarm_config.high_high",
                    "High-high limit must be greater than high limit"
                ))

        if "low" in limits and "low_low" in limits:
            if limits["low"] <= limits["low_low"]:
                errors.append(ValidationError(
                    "alarm_config.low",
                    "Low limit must be greater than low-low limit"
                ))

        if "high" in limits and "low" in limits:
            if limits["high"] <= limits["low"]:
                errors.append(ValidationError(
                    "alarm_config.high",
                    "High limit must be greater than low limit"
                ))

        return errors

    def _validate_validation_rules(self, rules: dict) -> List[ValidationError]:
        """Validate validation rules configuration"""
        errors = []

        # Rate of change validation
        roc = rules.get("rate_of_change", {})
        if roc.get("enabled"):
            max_per_second = roc.get("max_per_second")
            if max_per_second is None:
                errors.append(ValidationError(
                    "validation_rules.rate_of_change.max_per_second",
                    "Rate of change validation requires 'max_per_second' parameter"
                ))
            elif max_per_second <= 0:
                errors.append(ValidationError(
                    "validation_rules.rate_of_change.max_per_second",
                    "Max rate of change must be positive"
                ))

        # Range check validation
        range_check = rules.get("range_check", {})
        if range_check.get("enabled"):
            action = range_check.get("action")
            if action not in ["reject", "clamp"]:
                errors.append(ValidationError(
                    "validation_rules.range_check.action",
                    "Range check action must be 'reject' or 'clamp'"
                ))

        # Stuck value detection
        stuck_value = rules.get("stuck_value", {})
        if stuck_value.get("enabled"):
            max_same_count = stuck_value.get("max_same_count")
            if max_same_count is None:
                errors.append(ValidationError(
                    "validation_rules.stuck_value.max_same_count",
                    "Stuck value detection requires 'max_same_count' parameter"
                ))
            elif max_same_count < 2:
                errors.append(ValidationError(
                    "validation_rules.stuck_value.max_same_count",
                    "Max same count must be at least 2"
                ))

        return errors

    def validate_batch_points(
        self,
        tags: List[Tag],
        configs: Optional[List[PointConfiguration]] = None
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple points at once.

        Args:
            tags: List of Tags to validate
            configs: Optional list of PointConfigurations

        Returns:
            Dictionary mapping tag ID to ValidationResult
        """
        results = {}

        for i, tag in enumerate(tags):
            # Validate tag
            tag_result = self.validate_tag(tag)

            # Validate associated config if provided
            if configs and i < len(configs):
                config = configs[i]
                config_result = self.validate_point_configuration(config, tag)

                # Merge results
                tag_result.errors.extend(config_result.errors)
                tag_result.warnings.extend(config_result.warnings)
                if not config_result.is_valid:
                    tag_result.is_valid = False

            results[str(tag.id)] = tag_result

        return results

    def check_duplicate_addresses(
        self,
        tags: List[Tag],
        device_id: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Check for duplicate addresses in a list of tags.

        Args:
            tags: List of Tags to check
            device_id: Optional device ID to filter by

        Returns:
            List of tuples (address, tag_ids) for duplicates
        """
        duplicates = []
        address_map = {}

        for tag in tags:
            # Filter by device if specified
            if device_id and str(tag.device_id) != device_id:
                continue

            address = tag.address.lower()
            if address in address_map:
                address_map[address].append(str(tag.id))
            else:
                address_map[address] = [str(tag.id)]

        # Find duplicates
        for address, tag_ids in address_map.items():
            if len(tag_ids) > 1:
                duplicates.append((address, ", ".join(tag_ids)))

        return duplicates
