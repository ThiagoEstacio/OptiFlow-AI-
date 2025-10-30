"""
Root Cause Analysis Service

Identifies root causes of anomalies and issues:
- Correlation analysis across tags
- Time-lagged correlation detection
- Causal chain identification
- Automatic recommendations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy.stats import pearsonr
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Correlation Analysis

    Analyzes correlations between process variables
    """

    @staticmethod
    def calculate_correlation_matrix(
        data: pd.DataFrame,
        features: List[str]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix

        Args:
            data: Multivariate data
            features: Feature columns

        Returns:
            Correlation matrix
        """
        return data[features].corr(method='pearson')

    @staticmethod
    def find_correlated_tags(
        data: pd.DataFrame,
        target_tag: str,
        other_tags: List[str],
        threshold: float = 0.7,
        max_lag: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find tags correlated with target tag

        Args:
            data: Multivariate data
            target_tag: Target tag column
            other_tags: Other tag columns to check
            threshold: Correlation threshold (0-1)
            max_lag: Maximum time lag to check (in data points)

        Returns:
            List of correlated tags with correlation info
        """
        if target_tag not in data.columns:
            return []

        target_values = data[target_tag].dropna().values
        correlated_tags = []

        for other_tag in other_tags:
            if other_tag == target_tag or other_tag not in data.columns:
                continue

            other_values = data[other_tag].dropna().values

            # Synchronous correlation
            if len(target_values) == len(other_values) and len(target_values) > 2:
                try:
                    corr, p_value = pearsonr(target_values, other_values)

                    if abs(corr) >= threshold:
                        correlated_tags.append({
                            "tag": other_tag,
                            "correlation": float(corr),
                            "lag": 0,
                            "p_value": float(p_value),
                            "relationship": "positive" if corr > 0 else "negative"
                        })
                except:
                    pass

            # Time-lagged correlation
            for lag in range(1, max_lag + 1):
                if lag < len(target_values) and lag < len(other_values):
                    try:
                        # Check if other_tag leads target_tag
                        corr_lead, p_lead = pearsonr(
                            target_values[lag:],
                            other_values[:-lag]
                        )

                        if abs(corr_lead) >= threshold:
                            correlated_tags.append({
                                "tag": other_tag,
                                "correlation": float(corr_lead),
                                "lag": -lag,  # Negative means other_tag leads
                                "p_value": float(p_lead),
                                "relationship": "positive" if corr_lead > 0 else "negative",
                                "causality": f"{other_tag} may cause {target_tag} (leads by {lag} points)"
                            })

                        # Check if target_tag leads other_tag
                        corr_lag, p_lag = pearsonr(
                            target_values[:-lag],
                            other_values[lag:]
                        )

                        if abs(corr_lag) >= threshold:
                            correlated_tags.append({
                                "tag": other_tag,
                                "correlation": float(corr_lag),
                                "lag": lag,  # Positive means target_tag leads
                                "p_value": float(p_lag),
                                "relationship": "positive" if corr_lag > 0 else "negative",
                                "causality": f"{target_tag} may cause {other_tag} (leads by {lag} points)"
                            })
                    except:
                        pass

        # Sort by absolute correlation
        correlated_tags.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return correlated_tags


class CausalChainAnalyzer:
    """
    Causal Chain Analysis

    Identifies causal chains in process variables
    """

    @staticmethod
    def find_causal_chains(
        data: pd.DataFrame,
        tags: List[str],
        correlation_threshold: float = 0.6,
        max_lag: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find causal chains

        Args:
            data: Multivariate data
            tags: Tag columns
            correlation_threshold: Minimum correlation
            max_lag: Maximum lag

        Returns:
            List of causal chains
        """
        analyzer = CorrelationAnalyzer()
        chains = []

        # Find all leading correlations
        leading_pairs = []

        for target_tag in tags:
            correlated = analyzer.find_correlated_tags(
                data=data,
                target_tag=target_tag,
                other_tags=tags,
                threshold=correlation_threshold,
                max_lag=max_lag
            )

            for corr_info in correlated:
                if corr_info["lag"] < 0:  # Other tag leads
                    leading_pairs.append({
                        "cause": corr_info["tag"],
                        "effect": target_tag,
                        "lag": abs(corr_info["lag"]),
                        "correlation": corr_info["correlation"]
                    })

        # Build chains
        for pair in leading_pairs:
            chain = [pair["cause"], pair["effect"]]
            chain_lags = [pair["lag"]]
            chain_correlations = [pair["correlation"]]

            # Try to extend chain
            for other_pair in leading_pairs:
                if other_pair["cause"] == chain[-1] and other_pair["effect"] not in chain:
                    chain.append(other_pair["effect"])
                    chain_lags.append(other_pair["lag"])
                    chain_correlations.append(other_pair["correlation"])

            if len(chain) >= 2:
                chains.append({
                    "chain": chain,
                    "lags": chain_lags,
                    "correlations": chain_correlations,
                    "length": len(chain),
                    "avg_correlation": float(np.mean(chain_correlations))
                })

        # Sort by chain length and correlation
        chains.sort(key=lambda x: (x["length"], x["avg_correlation"]), reverse=True)

        return chains


class RootCauseAnalysisService:
    """
    Root Cause Analysis Service

    Main service for root cause identification
    """

    def __init__(self):
        self.correlation_analyzer = CorrelationAnalyzer()
        self.causal_chain_analyzer = CausalChainAnalyzer()

    def analyze_anomaly(
        self,
        anomaly_tag_id: str,
        anomaly_tag_name: str,
        anomaly_timestamp: datetime,
        all_tags_data: pd.DataFrame,
        tag_metadata: Dict[str, str],
        time_window_minutes: int = 60,
        correlation_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Analyze root cause of an anomaly

        Args:
            anomaly_tag_id: Tag with anomaly
            anomaly_tag_name: Tag name
            anomaly_timestamp: When anomaly occurred
            all_tags_data: Data for all related tags
            tag_metadata: Mapping of tag_id to tag_name
            time_window_minutes: Analysis window around anomaly
            correlation_threshold: Correlation threshold

        Returns:
            Root cause analysis results
        """
        results = {
            "anomaly_tag_id": anomaly_tag_id,
            "anomaly_tag_name": anomaly_tag_name,
            "anomaly_timestamp": anomaly_timestamp.isoformat(),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

        # Extract time window around anomaly
        start_time = anomaly_timestamp - timedelta(minutes=time_window_minutes)
        end_time = anomaly_timestamp + timedelta(minutes=time_window_minutes // 2)

        if 'timestamp' in all_tags_data.columns:
            window_data = all_tags_data[
                (all_tags_data['timestamp'] >= start_time) &
                (all_tags_data['timestamp'] <= end_time)
            ]
        else:
            window_data = all_tags_data

        if window_data.empty:
            results["error"] = "Insufficient data for analysis"
            return results

        # Get tag columns
        tag_columns = [col for col in window_data.columns if col.startswith('tag_') or col == anomaly_tag_id]

        if not tag_columns:
            results["error"] = "No tag data found"
            return results

        # Find correlated tags
        correlated_tags = self.correlation_analyzer.find_correlated_tags(
            data=window_data,
            target_tag=anomaly_tag_id,
            other_tags=tag_columns,
            threshold=correlation_threshold,
            max_lag=10
        )

        results["correlated_tags"] = correlated_tags[:10]  # Top 10

        # Find causal chains
        causal_chains = self.causal_chain_analyzer.find_causal_chains(
            data=window_data,
            tags=tag_columns,
            correlation_threshold=correlation_threshold,
            max_lag=5
        )

        # Filter chains containing anomaly tag
        relevant_chains = [
            chain for chain in causal_chains
            if anomaly_tag_id in chain["chain"]
        ]

        results["causal_chains"] = relevant_chains[:5]  # Top 5

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(
            anomaly_tag_name,
            correlated_tags,
            relevant_chains,
            tag_metadata
        )

        # Identify likely root causes
        results["likely_root_causes"] = self._identify_root_causes(
            anomaly_tag_id,
            correlated_tags,
            relevant_chains
        )

        return results

    def _identify_root_causes(
        self,
        anomaly_tag_id: str,
        correlated_tags: List[Dict[str, Any]],
        causal_chains: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify likely root causes"""

        root_causes = []

        # Tags that lead the anomaly tag (negative lag)
        leading_tags = [
            tag for tag in correlated_tags
            if tag.get("lag", 0) < 0
        ]

        for tag in leading_tags[:5]:
            root_causes.append({
                "tag": tag["tag"],
                "confidence": abs(tag["correlation"]),
                "lag_minutes": abs(tag.get("lag", 0)),
                "reason": f"Strong leading correlation ({tag['correlation']:.2f})",
                "type": "leading_indicator"
            })

        # Tags at the start of causal chains
        for chain in causal_chains:
            if anomaly_tag_id in chain["chain"]:
                root_tag = chain["chain"][0]

                if root_tag != anomaly_tag_id:
                    root_causes.append({
                        "tag": root_tag,
                        "confidence": chain["avg_correlation"],
                        "reason": f"Start of causal chain: {' → '.join(chain['chain'])}",
                        "type": "causal_chain_root"
                    })

        # Remove duplicates and sort by confidence
        seen_tags = set()
        unique_root_causes = []

        for rc in root_causes:
            if rc["tag"] not in seen_tags:
                seen_tags.add(rc["tag"])
                unique_root_causes.append(rc)

        unique_root_causes.sort(key=lambda x: x["confidence"], reverse=True)

        return unique_root_causes[:5]

    def _generate_recommendations(
        self,
        anomaly_tag_name: str,
        correlated_tags: List[Dict[str, Any]],
        causal_chains: List[Dict[str, Any]],
        tag_metadata: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on analysis"""

        recommendations = []

        if correlated_tags:
            leading_tags = [t for t in correlated_tags if t.get("lag", 0) < 0]

            if leading_tags:
                tag_names = [tag_metadata.get(t["tag"], t["tag"]) for t in leading_tags[:3]]

                recommendations.append({
                    "priority": "high",
                    "action": f"Investigate {', '.join(tag_names)}",
                    "reason": f"These variables changed before {anomaly_tag_name} anomaly",
                    "type": "investigation"
                })

        if causal_chains:
            for chain in causal_chains[:2]:
                chain_names = [tag_metadata.get(t, t) for t in chain["chain"]]

                recommendations.append({
                    "priority": "medium",
                    "action": f"Review process flow: {' → '.join(chain_names)}",
                    "reason": "Causal chain identified",
                    "type": "process_review"
                })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "action": "Review local conditions and recent changes",
                "reason": "No strong correlations found with other variables",
                "type": "local_investigation"
            })

        return recommendations


# Singleton instance
_root_cause_analysis_service = None


def get_root_cause_analysis_service() -> RootCauseAnalysisService:
    """Get singleton instance of Root Cause Analysis Service"""
    global _root_cause_analysis_service

    if _root_cause_analysis_service is None:
        _root_cause_analysis_service = RootCauseAnalysisService()

    return _root_cause_analysis_service
