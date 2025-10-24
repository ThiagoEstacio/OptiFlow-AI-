"""
AI Insights Engine - Generates intelligent insights from operational data
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class InsightsEngine:
    """
    AI-powered insights engine for generating actionable intelligence
    """

    def __init__(self):
        self.insights_history = []

    async def analyze_operation(
        self,
        operation_id: str,
        operation_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze a loading operation and generate insights

        Args:
            operation_id: Loading operation ID
            operation_data: Operation data including metrics

        Returns:
            List of insights
        """
        insights = []

        # Efficiency insight
        if 'efficiency_percentage' in operation_data:
            efficiency = operation_data['efficiency_percentage']

            if efficiency < 70:
                insights.append({
                    "type": "warning",
                    "category": "efficiency",
                    "title": "Low Loading Efficiency Detected",
                    "description": f"Loading efficiency is {efficiency:.1f}%, below target of 85%",
                    "recommendation": "Review equipment performance and identify bottlenecks",
                    "priority": "high",
                    "impact": "operational"
                })
            elif efficiency >= 90:
                insights.append({
                    "type": "success",
                    "category": "efficiency",
                    "title": "Excellent Loading Performance",
                    "description": f"Loading efficiency achieved {efficiency:.1f}%",
                    "recommendation": "Document best practices for replication",
                    "priority": "low",
                    "impact": "operational"
                })

        # Downtime insight
        if 'total_downtime_minutes' in operation_data:
            downtime = operation_data['total_downtime_minutes']

            if downtime > 60:
                insights.append({
                    "type": "alert",
                    "category": "downtime",
                    "title": "Significant Downtime Detected",
                    "description": f"Total downtime: {downtime} minutes",
                    "recommendation": "Investigate root causes and implement preventive measures",
                    "priority": "high",
                    "impact": "productivity"
                })

        # Energy insight
        if 'energy_per_ton' in operation_data and operation_data['energy_per_ton']:
            energy_per_ton = operation_data['energy_per_ton']
            benchmark = 2.5  # kWh/ton (example benchmark)

            if energy_per_ton > benchmark * 1.2:
                insights.append({
                    "type": "warning",
                    "category": "energy",
                    "title": "High Energy Consumption",
                    "description": f"Energy usage: {energy_per_ton:.2f} kWh/ton (20% above benchmark)",
                    "recommendation": "Optimize equipment setpoints and check for mechanical issues",
                    "priority": "medium",
                    "impact": "cost"
                })

        # Rate insight
        if 'actual_loading_rate' in operation_data and 'target_loading_rate' in operation_data:
            actual_rate = operation_data['actual_loading_rate']
            target_rate = operation_data['target_loading_rate']

            if target_rate and actual_rate < target_rate * 0.8:
                insights.append({
                    "type": "warning",
                    "category": "productivity",
                    "title": "Loading Rate Below Target",
                    "description": f"Actual: {actual_rate:.1f} t/h, Target: {target_rate:.1f} t/h",
                    "recommendation": "Check conveyor speeds and material flow conditions",
                    "priority": "high",
                    "impact": "productivity"
                })

        return insights

    async def detect_patterns(
        self,
        historical_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns in historical operational data

        Args:
            historical_data: Historical time series data

        Returns:
            List of detected patterns
        """
        patterns = []

        # Example: Detect recurring downtime patterns
        # This would use more sophisticated ML in production
        if 'downtime_minutes' in historical_data.columns:
            avg_downtime = historical_data['downtime_minutes'].mean()

            if avg_downtime > 30:
                patterns.append({
                    "type": "pattern",
                    "category": "recurring_issue",
                    "title": "Recurring Downtime Pattern",
                    "description": f"Average downtime per operation: {avg_downtime:.1f} minutes",
                    "recommendation": "Implement predictive maintenance program",
                    "frequency": "recurring",
                    "impact": "high"
                })

        return patterns

    async def find_opportunities(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify optimization opportunities

        Args:
            current_metrics: Current performance metrics
            historical_metrics: Historical performance metrics

        Returns:
            List of opportunities
        """
        opportunities = []

        # Energy optimization opportunity
        if 'energy_per_ton' in current_metrics and 'energy_per_ton' in historical_metrics:
            current_energy = current_metrics['energy_per_ton']
            best_energy = historical_metrics.get('min_energy_per_ton', current_energy)

            if current_energy > best_energy * 1.1:
                potential_savings = (current_energy - best_energy) * current_metrics.get('total_tons', 0)

                opportunities.append({
                    "type": "opportunity",
                    "category": "energy_optimization",
                    "title": "Energy Efficiency Improvement Opportunity",
                    "description": f"Current consumption could be reduced by {((current_energy/best_energy - 1) * 100):.1f}%",
                    "potential_value": f"{potential_savings:.0f} kWh savings",
                    "recommendation": "Apply setpoints from best-performing operations",
                    "priority": "medium"
                })

        return opportunities

    def generate_summary(self, insights: List[Dict[str, Any]]) -> str:
        """
        Generate natural language summary of insights

        Args:
            insights: List of insights

        Returns:
            Text summary
        """
        if not insights:
            return "All systems operating normally. No significant issues detected."

        summary_parts = []

        # Count by type
        warnings = [i for i in insights if i['type'] == 'warning']
        alerts = [i for i in insights if i['type'] == 'alert']
        opportunities = [i for i in insights if i['type'] == 'opportunity']

        if alerts:
            summary_parts.append(f"⚠️ {len(alerts)} critical alert(s) require immediate attention.")

        if warnings:
            summary_parts.append(f"⚡ {len(warnings)} warning(s) detected.")

        if opportunities:
            summary_parts.append(f"💡 {len(opportunities)} optimization opportunit{'y' if len(opportunities) == 1 else 'ies'} identified.")

        return " ".join(summary_parts)
