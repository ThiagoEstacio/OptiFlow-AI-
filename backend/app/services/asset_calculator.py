"""
Asset Attribute Calculator Service
Evaluates formulas for calculated attributes

Supports expressions like:
- tag('TAG_NAME') - Reference tag values
- attr('ATTRIBUTE_NAME') - Reference other attribute values
- Mathematical operations: +, -, *, /, **, %
- Functions: abs(), round(), min(), max(), sqrt(), pow()
- Comparisons: ==, !=, <, >, <=, >=
- Logical: and, or, not

Examples:
- Efficiency: "(tag('MOTOR_SPEED') / attr('Nominal Speed')) * 100"
- Power: "tag('VOLTAGE') * tag('CURRENT')"
- Average: "(tag('SENSOR_1') + tag('SENSOR_2')) / 2"
"""

import re
import math
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tag import Tag
from app.models.asset import Asset, AssetAttribute


class FormulaEvaluationError(Exception):
    """Raised when formula evaluation fails"""
    pass


class AssetAttributeCalculator:
    """Calculator for evaluating asset attribute formulas"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._tag_cache: Dict[str, Any] = {}
        self._attr_cache: Dict[str, Any] = {}

    async def evaluate_attribute(
        self,
        asset_id: str,
        attribute_name: str
    ) -> Optional[float]:
        """
        Evaluate a calculated attribute for an asset

        Args:
            asset_id: Asset UUID
            attribute_name: Name of the calculated attribute

        Returns:
            Calculated value or None if evaluation fails
        """
        # Get the attribute
        stmt = select(AssetAttribute).where(
            AssetAttribute.asset_id == asset_id,
            AssetAttribute.name == attribute_name,
            AssetAttribute.attribute_type == 'calculated'
        )
        result = await self.db.execute(stmt)
        attribute = result.scalar_one_or_none()

        if not attribute or not attribute.formula:
            return None

        try:
            return await self.evaluate_formula(attribute.formula, asset_id)
        except Exception as e:
            print(f"Error evaluating formula for {attribute_name}: {e}")
            return None

    async def evaluate_formula(
        self,
        formula: str,
        asset_id: str
    ) -> float:
        """
        Evaluate a formula string

        Args:
            formula: Formula string (e.g., "tag('SPEED') / 100")
            asset_id: Asset ID for context

        Returns:
            Evaluated result

        Raises:
            FormulaEvaluationError: If evaluation fails
        """
        # Clear caches for fresh evaluation
        self._tag_cache = {}
        self._attr_cache = {}

        try:
            # Replace tag() and attr() function calls with values
            processed_formula = await self._preprocess_formula(formula, asset_id)

            # Evaluate the expression safely
            result = self._safe_eval(processed_formula)

            return float(result)

        except Exception as e:
            raise FormulaEvaluationError(f"Formula evaluation failed: {str(e)}")

    async def _preprocess_formula(self, formula: str, asset_id: str) -> str:
        """
        Replace tag() and attr() calls with actual values

        Args:
            formula: Original formula
            asset_id: Asset ID for context

        Returns:
            Formula with values substituted
        """
        # Find all tag() calls
        tag_pattern = r"tag\(['\"]([^'\"]+)['\"]\)"
        tag_matches = re.findall(tag_pattern, formula)

        for tag_name in tag_matches:
            value = await self._get_tag_value(tag_name)
            # Replace the function call with the value
            formula = re.sub(
                rf"tag\(['\"]{ re.escape(tag_name)}['\"]\)",
                str(value),
                formula
            )

        # Find all attr() calls
        attr_pattern = r"attr\(['\"]([^'\"]+)['\"]\)"
        attr_matches = re.findall(attr_pattern, formula)

        for attr_name in attr_matches:
            value = await self._get_attribute_value(asset_id, attr_name)
            # Replace the function call with the value
            formula = re.sub(
                rf"attr\(['\"]{ re.escape(attr_name)}['\"]\)",
                str(value),
                formula
            )

        return formula

    async def _get_tag_value(self, tag_name: str) -> float:
        """
        Get current value of a tag

        Args:
            tag_name: Tag name

        Returns:
            Tag value (last_value)

        Raises:
            FormulaEvaluationError: If tag not found or no value
        """
        # Check cache
        if tag_name in self._tag_cache:
            return self._tag_cache[tag_name]

        # Query database
        stmt = select(Tag).where(Tag.name == tag_name)
        result = await self.db.execute(stmt)
        tag = result.scalar_one_or_none()

        if not tag:
            raise FormulaEvaluationError(f"Tag not found: {tag_name}")

        if tag.last_value is None:
            raise FormulaEvaluationError(f"Tag has no value: {tag_name}")

        try:
            value = float(tag.last_value)
        except (ValueError, TypeError):
            raise FormulaEvaluationError(f"Tag value is not numeric: {tag_name} = {tag.last_value}")

        # Cache the value
        self._tag_cache[tag_name] = value

        return value

    async def _get_attribute_value(self, asset_id: str, attr_name: str) -> float:
        """
        Get value of an attribute (static or tag reference)

        Args:
            asset_id: Asset UUID
            attr_name: Attribute name

        Returns:
            Attribute value

        Raises:
            FormulaEvaluationError: If attribute not found or invalid
        """
        # Check cache
        cache_key = f"{asset_id}:{attr_name}"
        if cache_key in self._attr_cache:
            return self._attr_cache[cache_key]

        # Query database
        stmt = select(AssetAttribute).where(
            AssetAttribute.asset_id == asset_id,
            AssetAttribute.name == attr_name
        )
        result = await self.db.execute(stmt)
        attribute = result.scalar_one_or_none()

        if not attribute:
            raise FormulaEvaluationError(f"Attribute not found: {attr_name}")

        value: Optional[float] = None

        if attribute.attribute_type == 'static':
            # Parse static value
            if not attribute.static_value:
                raise FormulaEvaluationError(f"Static attribute has no value: {attr_name}")

            try:
                value = float(attribute.static_value)
            except (ValueError, TypeError):
                raise FormulaEvaluationError(
                    f"Static attribute value is not numeric: {attr_name} = {attribute.static_value}"
                )

        elif attribute.attribute_type == 'tag_reference':
            # Get tag value
            if not attribute.tag_id:
                raise FormulaEvaluationError(f"Tag reference has no tag_id: {attr_name}")

            stmt = select(Tag).where(Tag.id == attribute.tag_id)
            result = await self.db.execute(stmt)
            tag = result.scalar_one_or_none()

            if not tag:
                raise FormulaEvaluationError(f"Referenced tag not found for attribute: {attr_name}")

            if tag.last_value is None:
                raise FormulaEvaluationError(f"Referenced tag has no value: {attr_name}")

            try:
                value = float(tag.last_value)
            except (ValueError, TypeError):
                raise FormulaEvaluationError(
                    f"Referenced tag value is not numeric: {attr_name} via {tag.name}"
                )

        elif attribute.attribute_type == 'calculated':
            # Recursively evaluate calculated attribute
            # Note: Be careful of circular references!
            if not attribute.formula:
                raise FormulaEvaluationError(f"Calculated attribute has no formula: {attr_name}")

            value = await self.evaluate_formula(attribute.formula, asset_id)

        else:
            raise FormulaEvaluationError(f"Unknown attribute type: {attribute.attribute_type}")

        if value is None:
            raise FormulaEvaluationError(f"Could not get value for attribute: {attr_name}")

        # Cache the value
        self._attr_cache[cache_key] = value

        return value

    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate a mathematical expression

        Args:
            expression: Math expression (numbers and operators only)

        Returns:
            Result of evaluation

        Raises:
            FormulaEvaluationError: If evaluation fails or contains unsafe code
        """
        # Allowed names in eval context (safe math functions)
        allowed_names = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sqrt': math.sqrt,
            'pow': pow,
            'floor': math.floor,
            'ceil': math.ceil,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }

        # Check for dangerous patterns
        dangerous_patterns = [
            '__', 'import', 'exec', 'eval', 'compile', 'open',
            'file', 'input', 'raw_input', '__builtins__'
        ]

        for pattern in dangerous_patterns:
            if pattern in expression:
                raise FormulaEvaluationError(f"Forbidden pattern in formula: {pattern}")

        try:
            # Evaluate with restricted globals and locals
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return result
        except SyntaxError as e:
            raise FormulaEvaluationError(f"Syntax error in formula: {str(e)}")
        except NameError as e:
            raise FormulaEvaluationError(f"Unknown function or variable: {str(e)}")
        except ZeroDivisionError:
            raise FormulaEvaluationError("Division by zero")
        except Exception as e:
            raise FormulaEvaluationError(f"Evaluation error: {str(e)}")

    async def evaluate_all_calculated_attributes(
        self,
        asset_id: str
    ) -> Dict[str, Optional[float]]:
        """
        Evaluate all calculated attributes for an asset

        Args:
            asset_id: Asset UUID

        Returns:
            Dictionary mapping attribute name to calculated value
        """
        # Get all calculated attributes for the asset
        stmt = select(AssetAttribute).where(
            AssetAttribute.asset_id == asset_id,
            AssetAttribute.attribute_type == 'calculated'
        )
        result = await self.db.execute(stmt)
        calc_attributes = result.scalars().all()

        results = {}

        for attr in calc_attributes:
            try:
                value = await self.evaluate_attribute(asset_id, attr.name)
                results[attr.name] = value
            except Exception as e:
                print(f"Error evaluating {attr.name}: {e}")
                results[attr.name] = None

        return results


# Utility function for easy import
async def evaluate_formula(
    db: AsyncSession,
    formula: str,
    asset_id: str
) -> float:
    """
    Convenience function to evaluate a formula

    Args:
        db: Database session
        formula: Formula string
        asset_id: Asset ID for context

    Returns:
        Evaluated result
    """
    calculator = AssetAttributeCalculator(db)
    return await calculator.evaluate_formula(formula, asset_id)
