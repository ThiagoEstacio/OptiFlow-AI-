"""
Feature Engineering Service - Asset-Based ML Features
======================================================

Extracts and calculates ML features from Asset Framework:
- Reads AssetAttributes (tag_reference, static, calculated)
- Evaluates formulas for derived features
- Considers cross-equipment correlations via process_flow
- Provides dynamic feature extraction for anomaly detection

Features are extracted from:
1. Tag References: Real-time values from InfluxDB/sensors
2. Static Values: Configuration values from Asset definitions
3. Calculated Values: Derived metrics using formulas

Formula Syntax:
- {attribute_name} - Reference to another attribute on same asset
- {parent.attribute_name} - Reference to parent asset attribute
- Standard math operations: +, -, *, /, **, %
- Functions: abs(), min(), max(), sqrt(), log()
- Conditionals: IF(condition, true_val, false_val)
"""

import logging
import re
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class FeatureResult:
    """Result of feature extraction for an asset"""
    asset_id: str
    asset_name: str
    equipment_type: str
    features: Dict[str, float]
    calculated_features: Dict[str, float]
    process_context: Dict[str, Any]
    timestamp: str
    warnings: List[str] = field(default_factory=list)

    def get_all_features(self) -> Dict[str, float]:
        """Returns combined features (raw + calculated)"""
        return {**self.features, **self.calculated_features}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "equipment_type": self.equipment_type,
            "features": self.features,
            "calculated_features": self.calculated_features,
            "all_features": self.get_all_features(),
            "process_context": self.process_context,
            "timestamp": self.timestamp,
            "warnings": self.warnings
        }


class FormulaEvaluator:
    """
    Evaluates calculated attribute formulas safely.

    Supported syntax:
    - {attr_name}: Reference to attribute value
    - Math: +, -, *, /, **, %
    - Functions: abs, min, max, sqrt, log, log10, sin, cos
    - IF(condition, true_val, false_val)
    """

    # Safe functions allowed in formulas
    SAFE_FUNCTIONS = {
        'abs': abs,
        'min': min,
        'max': max,
        'sqrt': math.sqrt,
        'log': math.log,
        'log10': math.log10,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'pow': pow,
        'round': round,
    }

    @classmethod
    def evaluate(
        cls,
        formula: str,
        context: Dict[str, float]
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Evaluate a formula with given context values.

        Args:
            formula: Formula string (e.g., "{power_kw} / {rated_power_kw} * 100")
            context: Dict of attribute names to values

        Returns:
            Tuple of (result, error_message)
        """
        if not formula:
            return None, "Empty formula"

        try:
            # Replace attribute references with values
            evaluated = formula

            # Find all {attribute} references
            attr_pattern = r'\{([^}]+)\}'
            matches = re.findall(attr_pattern, evaluated)

            for attr_name in matches:
                if attr_name in context:
                    value = context[attr_name]
                    # Replace {attr_name} with the numeric value
                    evaluated = evaluated.replace(f'{{{attr_name}}}', str(value))
                else:
                    return None, f"Missing attribute: {attr_name}"

            # Handle IF statements: IF(cond, true_val, false_val)
            if_pattern = r'IF\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
            while 'IF(' in evaluated.upper():
                match = re.search(if_pattern, evaluated, re.IGNORECASE)
                if match:
                    condition, true_val, false_val = match.groups()
                    # Evaluate condition
                    try:
                        cond_result = cls._safe_eval(condition)
                        result_val = true_val if cond_result else false_val
                        evaluated = evaluated[:match.start()] + str(result_val) + evaluated[match.end():]
                    except Exception as e:
                        return None, f"Error in IF condition: {e}"
                else:
                    break

            # Final evaluation
            result = cls._safe_eval(evaluated)

            if result is None:
                return None, "Evaluation returned None"

            return float(result), None

        except ZeroDivisionError:
            return None, "Division by zero"
        except ValueError as e:
            return None, f"Value error: {e}"
        except Exception as e:
            return None, f"Evaluation error: {e}"

    @classmethod
    def _safe_eval(cls, expression: str) -> float:
        """Safely evaluate a mathematical expression"""
        # Clean the expression
        expression = expression.strip()

        # Only allow safe characters
        allowed_chars = set('0123456789+-*/.()%<>=! ')
        allowed_chars.update(set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))

        if not all(c in allowed_chars for c in expression):
            raise ValueError(f"Invalid characters in expression: {expression}")

        # Create safe namespace with allowed functions
        safe_namespace = {
            '__builtins__': {},
            **cls.SAFE_FUNCTIONS
        }

        # Evaluate
        return eval(expression, safe_namespace)


class FeatureEngineeringService:
    """
    Feature Engineering Service for Asset-Based ML

    Responsibilities:
    1. Extract features from Asset attributes
    2. Calculate derived features using formulas
    3. Build process context from asset hierarchy
    4. Prepare feature vectors for ML models
    """

    # Default ML features if asset has no attributes
    DEFAULT_ML_FEATURES = [
        'vibration_mms',
        'temperature_c',
        'current_a',
        'power_kw',
        'load_pct'
    ]

    def __init__(self):
        """Initialize Feature Engineering Service"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "features_extracted": 0,
            "formulas_evaluated": 0,
            "cache_hits": 0
        }
        logger.info("🔧 FeatureEngineeringService initialized")

    async def extract_features(
        self,
        db: AsyncSession,
        equipment_id: str,
        live_readings: Optional[Dict[str, float]] = None
    ) -> FeatureResult:
        """
        Extract ML features for an equipment asset.

        Args:
            db: Database session
            equipment_id: Equipment ID (can be asset name or UUID)
            live_readings: Optional dict of live sensor readings

        Returns:
            FeatureResult with all extracted and calculated features
        """
        from app.models.asset import Asset, AssetAttribute, AssetType

        timestamp = datetime.now(timezone.utc).isoformat()
        warnings = []

        # Find the asset
        asset = await self._find_asset(db, equipment_id)

        if not asset:
            # Return default features from live_readings if asset not found
            logger.warning(f"Asset not found: {equipment_id}, using default features")
            return FeatureResult(
                asset_id=equipment_id,
                asset_name=equipment_id,
                equipment_type="unknown",
                features=live_readings or {},
                calculated_features={},
                process_context={},
                timestamp=timestamp,
                warnings=["Asset not found in Asset Framework, using raw readings"]
            )

        # Extract features from asset attributes
        features = {}
        calculated_features = {}
        static_values = {}

        # Build context from all attributes
        context = {}

        # First pass: collect tag_reference and static values
        for attr in asset.attributes:
            if attr.attribute_type == "tag_reference":
                # Get value from live_readings or default
                tag_name = attr.name
                if live_readings and tag_name in live_readings:
                    features[tag_name] = live_readings[tag_name]
                    context[tag_name] = live_readings[tag_name]
                elif live_readings:
                    # Try alternative name mappings
                    alt_names = self._get_alternative_names(tag_name)
                    for alt in alt_names:
                        if alt in live_readings:
                            features[tag_name] = live_readings[alt]
                            context[tag_name] = live_readings[alt]
                            break
                    else:
                        # Use 0 as default if not found
                        features[tag_name] = 0.0
                        context[tag_name] = 0.0
                        warnings.append(f"No value for tag: {tag_name}")

            elif attr.attribute_type == "static":
                # Parse static value
                try:
                    value = float(attr.static_value) if attr.static_value else 0.0
                    static_values[attr.name] = value
                    context[attr.name] = value
                except ValueError:
                    static_values[attr.name] = 0.0
                    context[attr.name] = 0.0
                    warnings.append(f"Invalid static value for {attr.name}: {attr.static_value}")

        # Second pass: evaluate calculated attributes
        for attr in asset.attributes:
            if attr.attribute_type == "calculated" and attr.formula:
                result, error = FormulaEvaluator.evaluate(attr.formula, context)
                if result is not None:
                    calculated_features[attr.name] = result
                    context[attr.name] = result  # Make available for other calculations
                    self._stats["formulas_evaluated"] += 1
                else:
                    warnings.append(f"Formula error for {attr.name}: {error}")

        # Build process context from asset metadata
        process_context = self._build_process_context(asset)

        self._stats["features_extracted"] += 1

        return FeatureResult(
            asset_id=str(asset.id),
            asset_name=asset.name,
            equipment_type=self._get_equipment_type(asset),
            features=features,
            calculated_features=calculated_features,
            process_context=process_context,
            timestamp=timestamp,
            warnings=warnings
        )

    async def get_correlated_features(
        self,
        db: AsyncSession,
        equipment_id: str,
        live_readings: Dict[str, Dict[str, float]]
    ) -> Dict[str, FeatureResult]:
        """
        Get features for an equipment and its correlated equipment.

        Uses process_flow metadata to identify upstream/downstream equipment.

        Args:
            db: Database session
            equipment_id: Primary equipment ID
            live_readings: Dict mapping equipment_id to readings

        Returns:
            Dict of equipment_id to FeatureResult
        """
        from app.models.asset import Asset

        results = {}

        # Get primary equipment features
        primary_result = await self.extract_features(
            db, equipment_id,
            live_readings.get(equipment_id, {})
        )
        results[equipment_id] = primary_result

        # Find correlated equipment from process_context
        process_flow = primary_result.process_context.get("process_flow", {})
        upstream = process_flow.get("upstream", [])
        downstream = process_flow.get("downstream", [])

        # Extract features for upstream equipment
        for up_id in upstream:
            if up_id not in results:
                up_result = await self.extract_features(
                    db, up_id,
                    live_readings.get(up_id, {})
                )
                results[up_id] = up_result

        # Extract features for downstream equipment
        for down_id in downstream:
            if down_id not in results:
                down_result = await self.extract_features(
                    db, down_id,
                    live_readings.get(down_id, {})
                )
                results[down_id] = down_result

        return results

    async def prepare_training_data(
        self,
        db: AsyncSession,
        equipment_id: str,
        historical_readings: List[Dict[str, Any]]
    ) -> List[Dict[str, float]]:
        """
        Prepare historical data for ML training with calculated features.

        Args:
            db: Database session
            equipment_id: Equipment to prepare data for
            historical_readings: List of historical sensor readings

        Returns:
            List of feature dicts ready for ML training
        """
        from app.models.asset import Asset

        # Find asset to get attribute definitions
        asset = await self._find_asset(db, equipment_id)

        if not asset or not asset.attributes:
            # Return raw readings if no asset attributes
            return historical_readings

        # Get static values (constant across all readings)
        static_context = {}
        formulas = {}

        for attr in asset.attributes:
            if attr.attribute_type == "static":
                try:
                    static_context[attr.name] = float(attr.static_value) if attr.static_value else 0.0
                except ValueError:
                    static_context[attr.name] = 0.0
            elif attr.attribute_type == "calculated" and attr.formula:
                formulas[attr.name] = attr.formula

        # Process each reading
        prepared_data = []

        for reading in historical_readings:
            # Build context with reading values and static values
            context = {**static_context}

            # Add tag values from reading
            for attr in asset.attributes:
                if attr.attribute_type == "tag_reference":
                    tag_name = attr.name
                    if tag_name in reading:
                        context[tag_name] = reading[tag_name]
                    else:
                        # Try alternative names
                        for alt in self._get_alternative_names(tag_name):
                            if alt in reading:
                                context[tag_name] = reading[alt]
                                break
                        else:
                            context[tag_name] = 0.0

            # Evaluate calculated features
            for calc_name, formula in formulas.items():
                result, _ = FormulaEvaluator.evaluate(formula, context)
                if result is not None:
                    context[calc_name] = result

            prepared_data.append(context)

        return prepared_data

    def get_ml_feature_columns(
        self,
        feature_result: FeatureResult
    ) -> List[str]:
        """
        Get the list of feature columns for ML from a FeatureResult.

        Filters out non-numeric and calculated ratio features that
        might cause data leakage.
        """
        all_features = feature_result.get_all_features()

        # ML-relevant features (exclude ratios that might cause leakage)
        ml_features = []

        for name, value in all_features.items():
            # Include primary sensor readings
            if any(key in name.lower() for key in [
                'vibration', 'temperature', 'temp', 'current',
                'power', 'load', 'pressure', 'flow', 'speed', 'rpm'
            ]):
                ml_features.append(name)

        # Add calculated features that are useful for ML
        for name in feature_result.calculated_features.keys():
            if name not in ml_features:
                # Include efficiency, ratios, and derived metrics
                if any(key in name.lower() for key in [
                    'efficiency', 'ratio', 'pct', 'percent',
                    'per_load', 'normalized', 'delta'
                ]):
                    ml_features.append(name)

        return ml_features

    async def _find_asset(
        self,
        db: AsyncSession,
        equipment_id: str
    ) -> Optional['Asset']:
        """Find asset by ID or name"""
        from app.models.asset import Asset

        # Try as UUID first
        try:
            asset_uuid = UUID(equipment_id)
            stmt = select(Asset).options(
                selectinload(Asset.attributes),
                selectinload(Asset.parent),
                selectinload(Asset.template)
            ).where(Asset.id == asset_uuid)
            result = await db.execute(stmt)
            asset = result.scalar_one_or_none()
            if asset:
                return asset
        except (ValueError, AttributeError):
            pass

        # Try by name
        stmt = select(Asset).options(
            selectinload(Asset.attributes),
            selectinload(Asset.parent),
            selectinload(Asset.template)
        ).where(Asset.name == equipment_id)
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()

        return asset

    def _get_alternative_names(self, attr_name: str) -> List[str]:
        """Get alternative names for an attribute (for mapping flexibility)"""
        # Common mappings
        mappings = {
            'vibration_mms': ['vibration', 'vib', 'vibration_mm_s'],
            'temperature_c': ['temperature', 'temp', 'temp_c', 'temperatura'],
            'current_a': ['current', 'corrente', 'i_motor'],
            'power_kw': ['power', 'potencia', 'p_motor'],
            'load_pct': ['load', 'carga', 'load_percent']
        }

        return mappings.get(attr_name, [])

    def _get_equipment_type(self, asset: 'Asset') -> str:
        """Get equipment type from asset template or metadata"""
        if asset.template:
            return asset.template.name

        # Try to infer from asset name
        name_lower = asset.name.lower()
        if 'motor' in name_lower:
            return 'motor'
        elif 'bomba' in name_lower or 'pump' in name_lower:
            return 'pump'
        elif 'correia' in name_lower or 'conveyor' in name_lower:
            return 'conveyor'
        elif 'britador' in name_lower or 'crusher' in name_lower:
            return 'crusher'
        elif 'elevador' in name_lower or 'elevator' in name_lower:
            return 'elevator'

        return 'equipment'

    def _build_process_context(self, asset: 'Asset') -> Dict[str, Any]:
        """Build process context from asset metadata"""
        # Calculate hierarchy level without recursion (count parent_id chain)
        hierarchy_level = 0
        if asset.parent:
            hierarchy_level = 1  # At least one parent

        context = {
            "hierarchy_level": hierarchy_level,
            "parent_name": asset.parent.name if asset.parent else None,
            "asset_type": str(asset.asset_type.value) if asset.asset_type else None,
        }

        # Add process_flow from metadata if available
        if asset.asset_metadata:
            if "process_flow" in asset.asset_metadata:
                context["process_flow"] = asset.asset_metadata["process_flow"]
            if "criticality" in asset.asset_metadata:
                context["criticality"] = asset.asset_metadata["criticality"]
            if "process_area" in asset.asset_metadata:
                context["process_area"] = asset.asset_metadata["process_area"]

        return context

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self._stats,
            "cache_size": len(self._cache)
        }


# Global singleton
_feature_service: Optional[FeatureEngineeringService] = None


def get_feature_engineering_service() -> FeatureEngineeringService:
    """Get global feature engineering service instance"""
    global _feature_service
    if _feature_service is None:
        _feature_service = FeatureEngineeringService()
    return _feature_service
