"""
Loading Operation Optimizer

Optimizes ship loading operations for maximum efficiency.

Optimizes:
- Berth allocation
- Loading sequence
- Equipment utilization
- Minimize waiting time
- Maximize throughput
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import heapq

from app.models.operational_data import ShipLoading, DailyOperations

logger = logging.getLogger(__name__)


class LoadingOptimizer:
    """
    Optimizes ship loading operations.

    Algorithms:
    - Berth allocation (minimize waiting time)
    - Loading sequence optimization
    - Equipment scheduling
    - Throughput maximization
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Port configuration
        self.num_berths = 4
        self.shiploaders_per_berth = 1
        self.target_loading_rate = 1200  # tons/hour
        self.berth_length_m = 300  # meters

    async def optimize_berth_allocation(
        self,
        site_id: int,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Optimize berth allocation for scheduled ships.

        Uses a greedy algorithm to minimize total waiting time.

        Args:
            site_id: Site ID
            days_ahead: Days to look ahead for scheduling

        Returns:
            Optimized berth allocation plan
        """
        try:
            logger.info(f"Optimizing berth allocation for next {days_ahead} days")

            # Get scheduled ships
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=days_ahead)

            result = await self.db.execute(
                select(ShipLoading).where(
                    and_(
                        ShipLoading.site_id == site_id,
                        ShipLoading.arrival_time >= start_date,
                        ShipLoading.arrival_time <= end_date,
                        ShipLoading.status.in_(["scheduled", "arrived"])
                    )
                ).order_by(ShipLoading.arrival_time)
            )
            ships = result.scalars().all()

            if not ships:
                return {
                    "status": "no_ships",
                    "message": "No ships scheduled for the period",
                    "allocations": [],
                }

            # Initialize berth availability
            berth_availability = {
                i: start_date for i in range(1, self.num_berths + 1)
            }

            allocations = []
            total_waiting_time = 0

            # Allocate each ship to best available berth
            for ship in ships:
                ship_dict = ship.to_dict()

                # Find berth that becomes available earliest
                best_berth = min(
                    berth_availability.items(),
                    key=lambda x: x[1]
                )[0]

                earliest_available = berth_availability[best_berth]
                arrival_time = ship.arrival_time

                # Calculate berthing time (when ship can actually berth)
                berthing_time = max(arrival_time, earliest_available)

                # Calculate waiting time
                if berthing_time > arrival_time:
                    waiting_hours = (berthing_time - arrival_time).total_seconds() / 3600
                else:
                    waiting_hours = 0

                total_waiting_time += waiting_hours

                # Estimate loading duration
                loading_hours = self._estimate_loading_duration(
                    ship.target_tonnage,
                    self.target_loading_rate
                )

                # Calculate departure time
                departure_time = berthing_time + timedelta(hours=loading_hours)

                # Update berth availability
                berth_availability[best_berth] = departure_time

                # Create allocation
                allocation = {
                    "ship_id": ship.id,
                    "ship_name": ship.ship_name,
                    "target_tonnage": ship.target_tonnage,
                    "arrival_time": arrival_time.isoformat(),
                    "allocated_berth": best_berth,
                    "berthing_time": berthing_time.isoformat(),
                    "estimated_loading_hours": round(loading_hours, 1),
                    "estimated_departure": departure_time.isoformat(),
                    "waiting_hours": round(waiting_hours, 1),
                }

                allocations.append(allocation)

            # Calculate optimization metrics
            avg_waiting_time = total_waiting_time / len(ships) if ships else 0
            berth_utilization = self._calculate_berth_utilization(
                allocations,
                days_ahead
            )

            return {
                "status": "success",
                "optimization_timestamp": datetime.utcnow().isoformat(),
                "period_days": days_ahead,
                "ships_scheduled": len(ships),
                "total_waiting_hours": round(total_waiting_time, 1),
                "average_waiting_hours": round(avg_waiting_time, 1),
                "berth_utilization_percent": berth_utilization,
                "allocations": allocations,
                "berth_schedule": self._format_berth_schedule(allocations),
            }

        except Exception as e:
            logger.error(f"Error optimizing berth allocation: {e}")
            raise

    async def optimize_loading_sequence(
        self,
        ship_loading_id: int
    ) -> Dict[str, Any]:
        """
        Optimize loading sequence for a ship.

        Determines optimal order of:
        - Which silos to use
        - Loading rates
        - Equipment scheduling

        Args:
            ship_loading_id: Ship loading operation ID

        Returns:
            Optimized loading sequence
        """
        try:
            # Get ship loading
            result = await self.db.execute(
                select(ShipLoading).where(ShipLoading.id == ship_loading_id)
            )
            ship = result.scalar_one_or_none()

            if not ship:
                raise ValueError(f"Ship loading {ship_loading_id} not found")

            logger.info(f"Optimizing loading sequence for {ship.ship_name}")

            # Simulate silo availability (in production would query actual silos)
            available_silos = self._get_available_silos(ship.product_type)

            # Calculate optimal sequence
            sequence = self._calculate_optimal_sequence(
                ship.target_tonnage,
                available_silos,
                self.target_loading_rate
            )

            # Estimate timeline
            timeline = self._estimate_loading_timeline(sequence)

            return {
                "ship_loading_id": ship_loading_id,
                "ship_name": ship.ship_name,
                "target_tonnage": ship.target_tonnage,
                "product_type": ship.product_type,
                "loading_sequence": sequence,
                "timeline": timeline,
                "total_estimated_hours": sum(step["duration_hours"] for step in sequence),
                "average_loading_rate": self.target_loading_rate,
                "optimized_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error optimizing loading sequence: {e}")
            raise

    async def calculate_optimal_loading_rate(
        self,
        ship_loading_id: int,
        current_weather: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal loading rate based on conditions.

        Considers:
        - Weather conditions
        - Equipment capacity
        - Product characteristics
        - Ship stability

        Args:
            ship_loading_id: Ship loading operation ID
            current_weather: Current weather conditions

        Returns:
            Recommended loading rate and factors
        """
        try:
            # Get ship loading
            result = await self.db.execute(
                select(ShipLoading).where(ShipLoading.id == ship_loading_id)
            )
            ship = result.scalar_one_or_none()

            if not ship:
                raise ValueError(f"Ship loading {ship_loading_id} not found")

            # Base loading rate
            optimal_rate = self.target_loading_rate

            factors = []
            adjustments = []

            # Weather adjustment
            if current_weather:
                wind_speed = current_weather.get("wind_speed_kmh", 0)
                if wind_speed > 60:
                    optimal_rate *= 0.5
                    adjustments.append({
                        "factor": "high_wind",
                        "adjustment": -50,
                        "reason": f"Wind speed {wind_speed} km/h exceeds safe limit",
                    })
                    factors.append("weather_delay")
                elif wind_speed > 40:
                    optimal_rate *= 0.7
                    adjustments.append({
                        "factor": "moderate_wind",
                        "adjustment": -30,
                        "reason": f"Wind speed {wind_speed} km/h - reduced rate for safety",
                    })

                if current_weather.get("rainfall_mm", 0) > 5:
                    optimal_rate *= 0.8
                    adjustments.append({
                        "factor": "rainfall",
                        "adjustment": -20,
                        "reason": "Heavy rainfall - protect product quality",
                    })
                    factors.append("weather_delay")

            # Product type adjustment
            if ship.product_type == "wheat":
                optimal_rate *= 0.9
                adjustments.append({
                    "factor": "product_sensitivity",
                    "adjustment": -10,
                    "reason": "Wheat requires careful handling",
                })

            # Ship DWT consideration
            if ship.ship_dwt and ship.ship_dwt < 30000:
                optimal_rate *= 0.85
                adjustments.append({
                    "factor": "small_ship",
                    "adjustment": -15,
                    "reason": "Smaller ship - reduced loading rate for stability",
                })

            # Calculate estimated completion
            estimated_hours = ship.target_tonnage / optimal_rate if optimal_rate > 0 else 0

            return {
                "ship_loading_id": ship_loading_id,
                "ship_name": ship.ship_name,
                "base_loading_rate": self.target_loading_rate,
                "optimal_loading_rate": round(optimal_rate, 1),
                "rate_efficiency": round((optimal_rate / self.target_loading_rate) * 100, 1),
                "target_tonnage": ship.target_tonnage,
                "estimated_hours": round(estimated_hours, 1),
                "adjustments": adjustments,
                "limiting_factors": factors,
                "calculated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating loading rate: {e}")
            raise

    def _estimate_loading_duration(
        self,
        tonnage: float,
        loading_rate: float
    ) -> float:
        """Estimate loading duration in hours."""
        if loading_rate <= 0:
            return 0

        # Base duration
        hours = tonnage / loading_rate

        # Add setup/teardown time (1 hour each)
        hours += 2

        return hours

    def _calculate_berth_utilization(
        self,
        allocations: List[Dict[str, Any]],
        period_days: int
    ) -> float:
        """Calculate average berth utilization percentage."""
        if not allocations:
            return 0.0

        total_berth_hours = self.num_berths * period_days * 24
        occupied_hours = sum(
            alloc["estimated_loading_hours"] for alloc in allocations
        )

        return round((occupied_hours / total_berth_hours) * 100, 1)

    def _format_berth_schedule(
        self,
        allocations: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Format allocations by berth for visualization."""
        schedule = {i: [] for i in range(1, self.num_berths + 1)}

        for alloc in allocations:
            berth = alloc["allocated_berth"]
            schedule[berth].append({
                "ship_name": alloc["ship_name"],
                "berthing_time": alloc["berthing_time"],
                "departure_time": alloc["estimated_departure"],
                "tonnage": alloc["target_tonnage"],
            })

        return schedule

    def _get_available_silos(self, product_type: str) -> List[Dict[str, Any]]:
        """Get available silos for product type (simulated)."""
        # In production, would query actual silo inventory
        return [
            {
                "silo_id": 1,
                "product_type": product_type,
                "available_tonnage": 5000,
                "loading_rate": 600,
            },
            {
                "silo_id": 2,
                "product_type": product_type,
                "available_tonnage": 8000,
                "loading_rate": 700,
            },
            {
                "silo_id": 3,
                "product_type": product_type,
                "available_tonnage": 6000,
                "loading_rate": 650,
            },
        ]

    def _calculate_optimal_sequence(
        self,
        target_tonnage: float,
        silos: List[Dict[str, Any]],
        target_rate: float
    ) -> List[Dict[str, Any]]:
        """Calculate optimal loading sequence using greedy algorithm."""
        sequence = []
        remaining_tonnage = target_tonnage

        # Sort silos by loading rate (highest first)
        sorted_silos = sorted(
            silos,
            key=lambda x: x["loading_rate"],
            reverse=True
        )

        step = 1
        for silo in sorted_silos:
            if remaining_tonnage <= 0:
                break

            # Use as much as possible from this silo
            tonnage_from_silo = min(
                silo["available_tonnage"],
                remaining_tonnage
            )

            duration_hours = tonnage_from_silo / silo["loading_rate"]

            sequence.append({
                "step": step,
                "silo_id": silo["silo_id"],
                "tonnage": tonnage_from_silo,
                "loading_rate": silo["loading_rate"],
                "duration_hours": round(duration_hours, 1),
            })

            remaining_tonnage -= tonnage_from_silo
            step += 1

        return sequence

    def _estimate_loading_timeline(
        self,
        sequence: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Estimate timeline for loading sequence."""
        timeline = []
        current_time = datetime.utcnow()

        for step in sequence:
            end_time = current_time + timedelta(hours=step["duration_hours"])

            timeline.append({
                "step": step["step"],
                "silo_id": step["silo_id"],
                "start_time": current_time.isoformat(),
                "end_time": end_time.isoformat(),
                "tonnage": step["tonnage"],
            })

            current_time = end_time

        return timeline
