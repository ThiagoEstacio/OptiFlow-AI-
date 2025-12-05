"""
MELH-007: Automatic Spare Parts Recommendation

Recommends spare parts based on:
- Historical parts usage for similar failures
- Equipment-specific parts lists
- Current inventory levels
- Lead time considerations
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)


class PartPriority(str, Enum):
    """Priority level for parts"""
    CRITICAL = "critical"  # Must have for repair
    RECOMMENDED = "recommended"  # Usually needed
    OPTIONAL = "optional"  # May be needed


@dataclass
class SparePart:
    """Spare part recommendation"""
    code: str
    description: str
    probability_needed: float  # 0.0 - 1.0
    priority: PartPriority
    current_stock: int
    reorder_point: int
    needs_order: bool
    estimated_cost: float
    lead_time_days: int
    supplier: Optional[str] = None
    last_used: Optional[datetime] = None


@dataclass
class PartRecommendation:
    """Complete parts recommendation for a failure"""
    equipment_id: str
    failure_type: str
    generated_at: datetime
    parts: List[SparePart]
    total_estimated_cost: float
    parts_in_stock: int
    parts_need_order: int
    confidence: float


class SparePartsRecommender:
    """
    Spare Parts Recommendation Service

    Uses historical maintenance data to recommend parts
    likely needed for a given equipment failure.
    """

    # Default parts catalog (would be loaded from database in production)
    PARTS_CATALOG = {
        # Mechanical parts
        "BRG001": {"description": "Bearing 6205-2RS", "cost": 45.00, "lead_time": 3, "category": "mechanical"},
        "BRG002": {"description": "Bearing 6206-2RS", "cost": 52.00, "lead_time": 3, "category": "mechanical"},
        "BRG003": {"description": "Bearing 6310-2RS", "cost": 125.00, "lead_time": 5, "category": "mechanical"},
        "SEAL001": {"description": "Oil Seal 35x52x7", "cost": 12.00, "lead_time": 2, "category": "mechanical"},
        "SEAL002": {"description": "Oil Seal 45x62x8", "cost": 15.00, "lead_time": 2, "category": "mechanical"},
        "BELT001": {"description": "V-Belt A68", "cost": 28.00, "lead_time": 1, "category": "mechanical"},
        "BELT002": {"description": "V-Belt B78", "cost": 35.00, "lead_time": 1, "category": "mechanical"},
        "COUP001": {"description": "Coupling Spider", "cost": 85.00, "lead_time": 5, "category": "mechanical"},

        # Electrical parts
        "CONT001": {"description": "Contactor 25A 3P", "cost": 120.00, "lead_time": 2, "category": "electrical"},
        "CONT002": {"description": "Contactor 40A 3P", "cost": 165.00, "lead_time": 2, "category": "electrical"},
        "RELAY001": {"description": "Thermal Overload Relay 16-24A", "cost": 95.00, "lead_time": 2, "category": "electrical"},
        "FUSE001": {"description": "Fuse 32A gG", "cost": 8.00, "lead_time": 1, "category": "electrical"},
        "CAP001": {"description": "Capacitor 25uF 450V", "cost": 45.00, "lead_time": 3, "category": "electrical"},

        # Instrumentation parts
        "SENS001": {"description": "Temperature Sensor PT100", "cost": 180.00, "lead_time": 5, "category": "instrumentation"},
        "SENS002": {"description": "Pressure Transmitter 0-10bar", "cost": 450.00, "lead_time": 7, "category": "instrumentation"},
        "SENS003": {"description": "Vibration Sensor", "cost": 320.00, "lead_time": 7, "category": "instrumentation"},
        "PROX001": {"description": "Proximity Sensor M18", "cost": 85.00, "lead_time": 2, "category": "instrumentation"},
    }

    # Historical usage patterns (would be learned from data)
    FAILURE_PARTS_HISTORY = {
        "mechanical": {
            "motor": ["BRG001", "BRG002", "SEAL001", "COUP001"],
            "pump": ["BRG002", "BRG003", "SEAL002", "COUP001"],
            "conveyor": ["BRG001", "BELT001", "BELT002"],
            "crusher": ["BRG003", "BELT002", "COUP001"],
            "default": ["BRG001", "SEAL001"]
        },
        "electrical": {
            "motor": ["CONT001", "RELAY001", "FUSE001", "CAP001"],
            "pump": ["CONT002", "RELAY001", "FUSE001"],
            "conveyor": ["CONT001", "RELAY001", "FUSE001"],
            "default": ["CONT001", "RELAY001", "FUSE001"]
        },
        "instrumentation": {
            "motor": ["SENS003", "SENS001"],
            "pump": ["SENS002", "SENS001"],
            "conveyor": ["PROX001", "SENS003"],
            "default": ["SENS001", "PROX001"]
        }
    }

    def __init__(self):
        """Initialize recommender"""
        self.recommendation_history: List[PartRecommendation] = []
        self._inventory_cache: Dict[str, int] = {}
        logger.info("SparePartsRecommender initialized")

    async def recommend(
        self,
        equipment_id: str,
        failure_type: str,
        include_optional: bool = True
    ) -> PartRecommendation:
        """
        Recommend spare parts for equipment failure.

        Args:
            equipment_id: Equipment identifier
            failure_type: Type of failure (mechanical, electrical, etc.)
            include_optional: Include optional parts in recommendations

        Returns:
            PartRecommendation with prioritized parts list
        """
        logger.info(f"Generating parts recommendation: {equipment_id}, failure: {failure_type}")

        # Determine equipment type from ID
        equipment_type = self._identify_equipment_type(equipment_id)

        # Get historical parts for this failure type and equipment
        historical_parts = await self._get_historical_parts(equipment_id, failure_type)

        # Get standard parts for this failure type
        standard_parts = self._get_standard_parts(failure_type, equipment_type)

        # Combine and rank parts
        all_parts = set(historical_parts + standard_parts)

        recommendations = []
        for part_code in all_parts:
            part_info = self.PARTS_CATALOG.get(part_code)
            if not part_info:
                continue

            # Calculate probability based on history
            history_count = historical_parts.count(part_code)
            probability = min(0.95, 0.5 + (history_count * 0.15))

            # Determine priority
            priority = self._determine_priority(part_code, failure_type, probability)

            if priority == PartPriority.OPTIONAL and not include_optional:
                continue

            # Get current stock
            stock = await self._get_current_stock(part_code)
            reorder_point = self._calculate_reorder_point(part_code)

            recommendations.append(SparePart(
                code=part_code,
                description=part_info["description"],
                probability_needed=probability,
                priority=priority,
                current_stock=stock,
                reorder_point=reorder_point,
                needs_order=stock < reorder_point,
                estimated_cost=part_info["cost"],
                lead_time_days=part_info["lead_time"],
                supplier=self._get_preferred_supplier(part_code)
            ))

        # Sort by priority and probability
        recommendations.sort(key=lambda p: (
            0 if p.priority == PartPriority.CRITICAL else 1 if p.priority == PartPriority.RECOMMENDED else 2,
            -p.probability_needed
        ))

        # Calculate totals
        total_cost = sum(p.estimated_cost for p in recommendations)
        in_stock = sum(1 for p in recommendations if p.current_stock >= 1)
        need_order = sum(1 for p in recommendations if p.needs_order)

        result = PartRecommendation(
            equipment_id=equipment_id,
            failure_type=failure_type,
            generated_at=datetime.utcnow(),
            parts=recommendations,
            total_estimated_cost=total_cost,
            parts_in_stock=in_stock,
            parts_need_order=need_order,
            confidence=self._calculate_confidence(recommendations, historical_parts)
        )

        # Cache recommendation
        self.recommendation_history.append(result)

        return result

    async def recommend_for_predicted_failure(
        self,
        equipment_id: str,
        predicted_failure_type: str,
        prediction_confidence: float
    ) -> PartRecommendation:
        """
        Proactive recommendation for predicted (not yet occurred) failure.

        Args:
            equipment_id: Equipment identifier
            predicted_failure_type: ML-predicted failure type
            prediction_confidence: Confidence of prediction (0-1)

        Returns:
            PartRecommendation with adjusted priorities
        """
        # Get base recommendation
        recommendation = await self.recommend(
            equipment_id,
            predicted_failure_type,
            include_optional=prediction_confidence > 0.7
        )

        # Adjust confidence based on prediction confidence
        recommendation.confidence *= prediction_confidence

        # Add proactive ordering flag to parts with low stock
        for part in recommendation.parts:
            if part.current_stock <= part.reorder_point and prediction_confidence > 0.6:
                part.needs_order = True

        return recommendation

    async def get_inventory_status(self) -> Dict[str, Any]:
        """
        Get current inventory status for all tracked parts.
        """
        inventory = []

        for part_code, part_info in self.PARTS_CATALOG.items():
            stock = await self._get_current_stock(part_code)
            reorder_point = self._calculate_reorder_point(part_code)

            inventory.append({
                "code": part_code,
                "description": part_info["description"],
                "category": part_info["category"],
                "current_stock": stock,
                "reorder_point": reorder_point,
                "status": "ok" if stock > reorder_point else "low" if stock > 0 else "out",
                "unit_cost": part_info["cost"],
                "lead_time_days": part_info["lead_time"]
            })

        # Summary
        total_parts = len(inventory)
        low_stock = sum(1 for p in inventory if p["status"] == "low")
        out_of_stock = sum(1 for p in inventory if p["status"] == "out")

        return {
            "parts": inventory,
            "summary": {
                "total_part_types": total_parts,
                "low_stock_count": low_stock,
                "out_of_stock_count": out_of_stock,
                "requires_attention": low_stock + out_of_stock
            }
        }

    async def _get_historical_parts(
        self,
        equipment_id: str,
        failure_type: str
    ) -> List[str]:
        """Get parts historically used for this equipment/failure combination"""
        # In production, this would query maintenance work order history
        # For now, return based on patterns

        equipment_type = self._identify_equipment_type(equipment_id)
        failure_category = failure_type.lower()

        if failure_category in self.FAILURE_PARTS_HISTORY:
            type_parts = self.FAILURE_PARTS_HISTORY[failure_category]
            return type_parts.get(equipment_type, type_parts.get("default", []))

        return []

    def _get_standard_parts(self, failure_type: str, equipment_type: str) -> List[str]:
        """Get standard parts for failure type"""
        failure_category = failure_type.lower()

        if failure_category in self.FAILURE_PARTS_HISTORY:
            type_parts = self.FAILURE_PARTS_HISTORY[failure_category]
            return type_parts.get(equipment_type, type_parts.get("default", []))

        return []

    def _identify_equipment_type(self, equipment_id: str) -> str:
        """Identify equipment type from ID"""
        id_lower = equipment_id.lower()

        if any(w in id_lower for w in ["motor", "mot", "mtr"]):
            return "motor"
        elif any(w in id_lower for w in ["pump", "pmp", "bomba"]):
            return "pump"
        elif any(w in id_lower for w in ["conv", "corr", "belt", "esteira"]):
            return "conveyor"
        elif any(w in id_lower for w in ["crush", "brit"]):
            return "crusher"
        else:
            return "default"

    def _determine_priority(
        self,
        part_code: str,
        failure_type: str,
        probability: float
    ) -> PartPriority:
        """Determine part priority"""
        # Critical parts based on category matching failure type
        part_info = self.PARTS_CATALOG.get(part_code, {})
        part_category = part_info.get("category", "")

        if part_category == failure_type.lower() and probability > 0.7:
            return PartPriority.CRITICAL
        elif probability > 0.5:
            return PartPriority.RECOMMENDED
        else:
            return PartPriority.OPTIONAL

    async def _get_current_stock(self, part_code: str) -> int:
        """Get current inventory level for part"""
        # In production, query inventory system
        # For now, return simulated values
        if part_code in self._inventory_cache:
            return self._inventory_cache[part_code]

        import random
        stock = random.randint(0, 10)
        self._inventory_cache[part_code] = stock
        return stock

    def _calculate_reorder_point(self, part_code: str) -> int:
        """Calculate reorder point based on lead time and usage"""
        part_info = self.PARTS_CATALOG.get(part_code, {})
        lead_time = part_info.get("lead_time", 3)

        # Reorder point = lead time demand + safety stock
        # Simplified: 2 units per week demand + 1 safety stock per lead time day
        return max(2, lead_time)

    def _get_preferred_supplier(self, part_code: str) -> str:
        """Get preferred supplier for part"""
        # Would query supplier database
        part_info = self.PARTS_CATALOG.get(part_code, {})
        category = part_info.get("category", "")

        suppliers = {
            "mechanical": "SKF Brasil",
            "electrical": "WEG Distribuidora",
            "instrumentation": "Emerson Process"
        }
        return suppliers.get(category, "General Supplier")

    def _calculate_confidence(
        self,
        recommendations: List[SparePart],
        historical_parts: List[str]
    ) -> float:
        """Calculate confidence in recommendation"""
        if not recommendations:
            return 0.5

        # Higher confidence if recommendations match history
        historical_match = sum(
            1 for p in recommendations
            if p.code in historical_parts
        ) / len(recommendations)

        return min(0.95, 0.5 + (historical_match * 0.45))

    def to_dict(self, recommendation: PartRecommendation) -> Dict[str, Any]:
        """Convert recommendation to dictionary"""
        return {
            "equipment_id": recommendation.equipment_id,
            "failure_type": recommendation.failure_type,
            "generated_at": recommendation.generated_at.isoformat(),
            "confidence": recommendation.confidence,
            "parts": [
                {
                    "code": p.code,
                    "description": p.description,
                    "probability_needed": round(p.probability_needed, 2),
                    "priority": p.priority.value,
                    "current_stock": p.current_stock,
                    "reorder_point": p.reorder_point,
                    "needs_order": p.needs_order,
                    "estimated_cost": p.estimated_cost,
                    "lead_time_days": p.lead_time_days,
                    "supplier": p.supplier
                }
                for p in recommendation.parts
            ],
            "summary": {
                "total_parts": len(recommendation.parts),
                "total_estimated_cost": recommendation.total_estimated_cost,
                "parts_in_stock": recommendation.parts_in_stock,
                "parts_need_order": recommendation.parts_need_order
            }
        }


# Singleton instance
_spare_parts_service: Optional[SparePartsRecommender] = None


def get_spare_parts_service() -> SparePartsRecommender:
    """Get or create spare parts service instance"""
    global _spare_parts_service
    if _spare_parts_service is None:
        _spare_parts_service = SparePartsRecommender()
    return _spare_parts_service
