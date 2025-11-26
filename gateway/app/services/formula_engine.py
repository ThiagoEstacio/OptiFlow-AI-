"""
Formula Engine - Executes calculated tag formulas
================================================

This engine evaluates formula expressions for calculated tags.
Supports:
- Event-based evaluation (when input tags change)
- Periodic evaluation (at configured interval)
- Safe expression evaluation with math functions
- Dependency tracking and cycle detection

Similar to PI Performance Equations or OSIsoft AF Analytics.
"""

import asyncio
import math
import logging
import time
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class FormulaEngine:
    """
    Engine for evaluating calculated tag formulas.

    Features:
    - Safe expression evaluation (restricted builtins)
    - Dependency tracking (which tags affect which formulas)
    - Event-driven evaluation (when inputs change)
    - Periodic evaluation (scheduled)
    - Cycle detection (prevents infinite loops)
    """

    # Safe builtins for formula evaluation
    SAFE_BUILTINS = {
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'sum': sum,
        'len': len,
        'pow': pow,
        'int': int,
        'float': float,
        'bool': bool,
        'True': True,
        'False': False,
        'None': None,
    }

    # Math functions available in formulas
    MATH_FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'floor': math.floor,
        'ceil': math.ceil,
        'pi': math.pi,
        'e': math.e,
    }

    def __init__(self):
        # Tag value cache: tag_name -> {value, quality, timestamp}
        self._tag_values: Dict[str, Dict[str, Any]] = {}

        # Formula definitions: tag_id -> FormulaConfig
        self._formulas: Dict[str, Any] = {}

        # Dependency map: input_tag -> set of formula_tag_ids that depend on it
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Reverse dependency map: formula_tag_id -> set of input_tags
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)

        # Callback for publishing calculated values
        self._publish_callback: Optional[Callable] = None

        # Running state
        self._running = False
        self._periodic_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            'evaluations': 0,
            'errors': 0,
            'last_evaluation': None,
            'avg_eval_time_ms': 0.0,
        }

        logger.info("Formula Engine initialized")

    def set_publish_callback(self, callback: Callable):
        """Set callback for publishing calculated values"""
        self._publish_callback = callback

    def register_formula(self, tag_id: str, formula_config: Any) -> bool:
        """
        Register a formula for a calculated tag.

        Args:
            tag_id: The tag ID for the calculated value
            formula_config: FormulaConfig object with expression and inputs

        Returns:
            True if registered successfully, False if cycle detected
        """
        if not formula_config or not formula_config.enabled:
            return False

        # Check for cycles before registering
        if self._would_create_cycle(tag_id, formula_config.input_tags):
            logger.error(f"Cycle detected! Cannot register formula for {tag_id}")
            return False

        # Store formula
        self._formulas[tag_id] = formula_config

        # Update dependency maps
        self._reverse_deps[tag_id] = set(formula_config.input_tags)

        for input_tag in formula_config.input_tags:
            self._dependencies[input_tag].add(tag_id)

        logger.info(f"Registered formula for {tag_id}: {formula_config.expression}")
        logger.debug(f"  Input tags: {formula_config.input_tags}")

        return True

    def unregister_formula(self, tag_id: str):
        """Remove a formula registration"""
        if tag_id in self._formulas:
            # Clean up dependency maps
            for input_tag in self._reverse_deps.get(tag_id, set()):
                self._dependencies[input_tag].discard(tag_id)

            del self._formulas[tag_id]
            self._reverse_deps.pop(tag_id, None)

            logger.info(f"Unregistered formula for {tag_id}")

    def _would_create_cycle(self, tag_id: str, input_tags: List[str]) -> bool:
        """Check if adding this formula would create a dependency cycle"""
        # BFS to check if any input_tag eventually depends on tag_id
        visited = set()
        queue = list(input_tags)

        while queue:
            current = queue.pop(0)
            if current == tag_id:
                return True  # Cycle detected!

            if current in visited:
                continue
            visited.add(current)

            # Check if current tag has a formula that depends on other tags
            if current in self._reverse_deps:
                queue.extend(self._reverse_deps[current])

        return False

    def update_tag_value(self, tag_name: str, value: Any, quality: str = "Good",
                         timestamp: Optional[datetime] = None):
        """
        Update a tag value in the cache and trigger dependent formulas.

        This is called when a real tag value changes.
        """
        self._tag_values[tag_name] = {
            'value': value,
            'quality': quality,
            'timestamp': timestamp or datetime.utcnow(),
        }

        # Find and evaluate dependent formulas
        dependent_formulas = self._dependencies.get(tag_name, set())

        for formula_tag_id in dependent_formulas:
            # Evaluate asynchronously to not block
            asyncio.create_task(self._evaluate_formula(formula_tag_id))

    async def _evaluate_formula(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate a single formula and publish the result.

        Returns:
            Dict with value, quality, timestamp or None on error
        """
        formula = self._formulas.get(tag_id)
        if not formula or not formula.enabled:
            return None

        start_time = time.time()

        try:
            # Build tags context with current values
            tags = {}
            all_inputs_good = True

            for input_tag in formula.input_tags:
                tag_data = self._tag_values.get(input_tag)
                if tag_data is None:
                    logger.warning(f"Formula {tag_id}: Input tag '{input_tag}' not found")
                    all_inputs_good = False
                    tags[input_tag] = None
                else:
                    tags[input_tag] = tag_data['value']
                    if tag_data['quality'] != 'Good':
                        all_inputs_good = False

            # Skip if any input is None
            if None in tags.values():
                logger.debug(f"Formula {tag_id}: Skipping - missing input values")
                return None

            # Evaluate expression
            result = self._safe_eval(formula.expression, tags)

            # Determine quality
            quality = 'Good' if all_inputs_good else 'Uncertain'

            # Build result
            eval_result = {
                'tag_id': tag_id,
                'value': result,
                'quality': quality,
                'timestamp': datetime.utcnow(),
                'calculated': True,
            }

            # Update cache with calculated value
            self._tag_values[tag_id] = eval_result

            # Publish result if callback set
            if self._publish_callback:
                await self._publish_callback(eval_result)

            # Update stats
            eval_time_ms = (time.time() - start_time) * 1000
            self._stats['evaluations'] += 1
            self._stats['last_evaluation'] = datetime.utcnow().isoformat()
            self._stats['avg_eval_time_ms'] = (
                (self._stats['avg_eval_time_ms'] * (self._stats['evaluations'] - 1) + eval_time_ms)
                / self._stats['evaluations']
            )

            logger.debug(f"Formula {tag_id} = {result} ({eval_time_ms:.2f}ms)")

            return eval_result

        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Formula evaluation error for {tag_id}: {e}")

            # Return error value if configured
            if formula.on_error_value is not None:
                return {
                    'tag_id': tag_id,
                    'value': formula.on_error_value,
                    'quality': str(formula.on_error_quality) if hasattr(formula, 'on_error_quality') else 'Bad',
                    'timestamp': datetime.utcnow(),
                    'calculated': True,
                    'error': str(e),
                }

            return None

    def _safe_eval(self, expression: str, tags: Dict[str, Any]) -> Any:
        """
        Safely evaluate a formula expression.

        Args:
            expression: Python-like expression (e.g., "tags['A'] * 2 + tags['B']")
            tags: Dictionary of tag values

        Returns:
            Evaluated result
        """
        # Build safe globals
        safe_globals = {
            '__builtins__': self.SAFE_BUILTINS,
            'math': type('math', (), self.MATH_FUNCTIONS)(),
            'tags': tags,
        }

        # Add math functions directly for convenience
        safe_globals.update(self.MATH_FUNCTIONS)

        # Evaluate
        result = eval(expression, safe_globals, {})

        return result

    async def evaluate_all(self):
        """Evaluate all registered formulas (for periodic evaluation)"""
        for tag_id in list(self._formulas.keys()):
            await self._evaluate_formula(tag_id)

    async def start_periodic_evaluation(self, interval_ms: int = 1000):
        """Start periodic evaluation of all formulas"""
        if self._running:
            return

        self._running = True

        async def periodic_loop():
            while self._running:
                await self.evaluate_all()
                await asyncio.sleep(interval_ms / 1000.0)

        self._periodic_task = asyncio.create_task(periodic_loop())
        logger.info(f"Started periodic formula evaluation every {interval_ms}ms")

    async def stop(self):
        """Stop the formula engine"""
        self._running = False
        if self._periodic_task:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass
        logger.info("Formula Engine stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            **self._stats,
            'registered_formulas': len(self._formulas),
            'cached_tags': len(self._tag_values),
        }

    def get_formula_info(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered formula"""
        formula = self._formulas.get(tag_id)
        if not formula:
            return None

        return {
            'tag_id': tag_id,
            'expression': formula.expression,
            'input_tags': formula.input_tags,
            'update_interval_ms': formula.update_interval_ms,
            'enabled': formula.enabled,
            'current_value': self._tag_values.get(tag_id, {}).get('value'),
            'dependents': list(self._dependencies.get(tag_id, set())),
        }

    def list_formulas(self) -> List[Dict[str, Any]]:
        """List all registered formulas"""
        return [self.get_formula_info(tag_id) for tag_id in self._formulas]


# Global instance
_formula_engine: Optional[FormulaEngine] = None


def get_formula_engine() -> FormulaEngine:
    """Get or create the global formula engine instance"""
    global _formula_engine
    if _formula_engine is None:
        _formula_engine = FormulaEngine()
    return _formula_engine
