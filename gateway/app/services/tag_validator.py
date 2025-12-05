"""
Tag Validator Service - CORR-002
================================

Validates tags configuration to prevent orphaned tags (tags pointing to non-existent adapters).
This is a critical data integrity check to ensure no false positives/negatives in the UI.

Features:
1. Validate tags have valid adapter references
2. Detect orphaned tags on startup
3. Prevent creation of tags for non-existent adapters
4. Report validation issues with clear error messages

Sprint 1 Task: CORR-002 - Tags can be created for non-existent adapters
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Critical - tag cannot function
    WARNING = "warning"  # Non-critical - tag may work with limitations
    INFO = "info"        # Informational - no immediate action needed


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: ValidationSeverity
    tag_id: str
    adapter_id: str
    message: str
    recommendation: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "tag_id": self.tag_id,
            "adapter_id": self.adapter_id,
            "message": self.message,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat()
        }


class TagValidator:
    """
    Validates tag configurations against available adapters.

    CORR-002: Prevents tags from being created/configured for non-existent adapters.
    """

    def __init__(self):
        self._issues: List[ValidationIssue] = []
        self._last_validation: Optional[datetime] = None
        self._valid_adapter_ids: set = set()

    def set_valid_adapters(self, adapter_ids: List[str]):
        """Update the list of valid adapter IDs"""
        self._valid_adapter_ids = set(adapter_ids)
        logger.info(f"📋 TagValidator: Registered {len(self._valid_adapter_ids)} valid adapters")

    def validate_tag(self, tag: Dict[str, Any]) -> Tuple[bool, Optional[ValidationIssue]]:
        """
        Validate a single tag configuration.

        Args:
            tag: Tag configuration dictionary

        Returns:
            Tuple of (is_valid, validation_issue_if_any)
        """
        tag_id = tag.get("tag_id") or tag.get("id") or tag.get("name", "unknown")
        adapter_id = tag.get("adapter_id") or tag.get("source")

        # Check if adapter_id is specified
        if not adapter_id:
            issue = ValidationIssue(
                severity=ValidationSeverity.ERROR,
                tag_id=tag_id,
                adapter_id="<not specified>",
                message="Tag has no adapter_id specified",
                recommendation="Specify a valid adapter_id for this tag"
            )
            return False, issue

        # Check if adapter exists
        if adapter_id not in self._valid_adapter_ids:
            issue = ValidationIssue(
                severity=ValidationSeverity.ERROR,
                tag_id=tag_id,
                adapter_id=adapter_id,
                message=f"Tag references non-existent adapter '{adapter_id}'",
                recommendation=f"Either create adapter '{adapter_id}' or update tag to use a valid adapter: {list(self._valid_adapter_ids)}"
            )
            return False, issue

        return True, None

    def validate_tags_config(self, tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a list of tag configurations.

        Args:
            tags: List of tag configuration dictionaries

        Returns:
            Validation report with issues and statistics
        """
        self._issues.clear()
        self._last_validation = datetime.utcnow()

        valid_count = 0
        invalid_count = 0
        orphaned_tags = []

        for tag in tags:
            is_valid, issue = self.validate_tag(tag)

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                if issue:
                    self._issues.append(issue)
                    orphaned_tags.append({
                        "tag_id": issue.tag_id,
                        "adapter_id": issue.adapter_id,
                        "message": issue.message
                    })

        # Log summary
        if invalid_count > 0:
            logger.warning(
                f"⚠️  Tag validation: {invalid_count} orphaned tags found "
                f"(out of {len(tags)} total)"
            )
            for issue in self._issues:
                logger.warning(f"   - {issue.tag_id}: {issue.message}")
        else:
            logger.info(f"✅ Tag validation: All {valid_count} tags are valid")

        return {
            "success": invalid_count == 0,
            "total_tags": len(tags),
            "valid_tags": valid_count,
            "invalid_tags": invalid_count,
            "orphaned_tags": orphaned_tags,
            "issues": [i.to_dict() for i in self._issues],
            "valid_adapters": list(self._valid_adapter_ids),
            "validation_timestamp": self._last_validation.isoformat()
        }

    def validate_tag_creation(
        self,
        tag: Dict[str, Any],
        raise_on_invalid: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a tag before creation (for API endpoints).

        CORR-002: This method should be called before creating any new tag.

        Args:
            tag: Tag configuration to validate
            raise_on_invalid: If True, raises ValueError on invalid tag

        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, issue = self.validate_tag(tag)

        if not is_valid and issue:
            error_msg = f"{issue.message}. {issue.recommendation}"

            if raise_on_invalid:
                raise ValueError(error_msg)

            return False, error_msg

        return True, None

    def get_orphaned_tags(self, tags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get list of orphaned tags (tags with invalid adapter references).

        Args:
            tags: List of tag configurations

        Returns:
            List of orphaned tag configurations
        """
        orphaned = []

        for tag in tags:
            is_valid, _ = self.validate_tag(tag)
            if not is_valid:
                orphaned.append(tag)

        return orphaned

    def cleanup_orphaned_tags(
        self,
        tags: List[Dict[str, Any]],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Remove orphaned tags from configuration.

        Args:
            tags: List of tag configurations
            dry_run: If True, only report what would be removed

        Returns:
            Cleanup report
        """
        orphaned = self.get_orphaned_tags(tags)

        if dry_run:
            return {
                "dry_run": True,
                "would_remove": len(orphaned),
                "would_keep": len(tags) - len(orphaned),
                "orphaned_tags": [
                    {
                        "tag_id": t.get("tag_id") or t.get("id") or t.get("name"),
                        "adapter_id": t.get("adapter_id") or t.get("source")
                    }
                    for t in orphaned
                ]
            }

        # Remove orphaned tags
        valid_tags = [t for t in tags if t not in orphaned]

        return {
            "dry_run": False,
            "removed": len(orphaned),
            "remaining": len(valid_tags),
            "valid_tags": valid_tags
        }

    def get_validation_report(self) -> Dict[str, Any]:
        """Get the last validation report"""
        return {
            "last_validation": self._last_validation.isoformat() if self._last_validation else None,
            "issues_count": len(self._issues),
            "issues": [i.to_dict() for i in self._issues],
            "valid_adapters": list(self._valid_adapter_ids)
        }


# Global validator instance
_validator_instance: Optional[TagValidator] = None


def get_tag_validator() -> TagValidator:
    """Get global tag validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = TagValidator()
    return _validator_instance


def validate_tags_on_startup(
    adapters_config_path: str = "/app/config/adapters_config.json",
    tags_config_path: str = "/app/config/tags_config.json"
) -> Dict[str, Any]:
    """
    Validate tags configuration on startup.

    This function should be called during Gateway initialization to detect
    any orphaned tags before they cause issues.

    Args:
        adapters_config_path: Path to adapters configuration file
        tags_config_path: Path to tags configuration file

    Returns:
        Validation report
    """
    validator = get_tag_validator()

    # Load adapters config
    adapters_path = Path(adapters_config_path)
    if adapters_path.exists():
        try:
            with open(adapters_path, 'r') as f:
                adapters_config = json.load(f)

            adapter_ids = [
                a.get("adapter_id")
                for a in adapters_config.get("adapters", [])
            ]
            validator.set_valid_adapters(adapter_ids)

        except Exception as e:
            logger.error(f"Failed to load adapters config: {e}")
            return {"success": False, "error": str(e)}
    else:
        logger.warning(f"Adapters config not found: {adapters_config_path}")
        return {"success": False, "error": "Adapters config not found"}

    # Load tags config
    tags_path = Path(tags_config_path)
    if tags_path.exists():
        try:
            with open(tags_path, 'r') as f:
                tags_config = json.load(f)

            tags = tags_config.get("tags", [])

            # Validate all tags
            report = validator.validate_tags_config(tags)

            return report

        except Exception as e:
            logger.error(f"Failed to load tags config: {e}")
            return {"success": False, "error": str(e)}
    else:
        logger.info(f"Tags config not found: {tags_config_path} (this is OK if using adapter-embedded tags)")
        return {"success": True, "total_tags": 0, "note": "No standalone tags config found"}


def validate_tag_for_creation(tag: Dict[str, Any], available_adapters: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a tag before creation.

    CORR-002: Use this in API endpoints that create tags.

    Args:
        tag: Tag configuration
        available_adapters: List of valid adapter IDs

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_tag_validator()
    validator.set_valid_adapters(available_adapters)

    return validator.validate_tag_creation(tag, raise_on_invalid=False)
