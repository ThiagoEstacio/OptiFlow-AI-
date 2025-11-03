#!/usr/bin/env python3
"""
OptiFlow AI - Machine Learning Capabilities Test Suite
Branch: claude/fix-autonomous-agent-sessions-011CUm8WUduocmLfq3bJpCxf

Tests all ML capabilities:
1. Anomaly Detection (Isolation Forest)
2. Time Series Forecasting (ARIMA, Prophet)
3. Pattern Recognition
4. Predictive Maintenance
5. Correlation Analysis
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# Configuration
BASE_URL = "http://localhost:8000"
RESULTS_DIR = "test_results"

class MLTester:
    """Test suite for Machine Learning capabilities"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []

    def test_anomaly_detection(self):
        """Test Anomaly Detection using Isolation Forest"""
        print("\n" + "="*70)
        print("TEST: Anomaly Detection (Isolation Forest)")
        print("="*70)

        test_cases = [
            {
                "name": "Normal Operating Range",
                "tag_id": "CORREIA_01_VELOCIDADE",
                "duration": "24h",
                "sensitivity": "medium",
                "expected_anomalies": "low"
            },
            {
                "name": "High Sensitivity Detection",
                "tag_id": "CORREIA_01_VELOCIDADE",
                "duration": "7d",
                "sensitivity": "high",
                "expected_anomalies": "medium"
            },
            {
                "name": "Multi-variate Anomaly",
                "tag_ids": ["CORREIA_01_VELOCIDADE", "CORREIA_01_CORRENTE"],
                "duration": "24h",
                "sensitivity": "medium",
                "expected_anomalies": "correlations"
            }
        ]

        for test in test_cases:
            print(f"\n  → {test['name']}")

            payload = {
                "tag_id": test.get("tag_id"),
                "tag_ids": test.get("tag_ids"),
                "duration": test["duration"],
                "sensitivity": test["sensitivity"]
            }

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ai-insights/detect-anomalies",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    anomaly_count = len(data.get("anomalies", []))
                    severity = data.get("severity_distribution", {})

                    print(f"    ✓ Anomalies detected: {anomaly_count}")
                    print(f"    ✓ Severity: {severity}")

                    # Analyze results
                    if anomaly_count > 0:
                        print(f"    ✓ Sample anomaly:")
                        sample = data["anomalies"][0]
                        print(f"      - Timestamp: {sample.get('timestamp')}")
                        print(f"      - Value: {sample.get('value')}")
                        print(f"      - Anomaly score: {sample.get('anomaly_score')}")

                    self.results.append({
                        "test": "anomaly_detection",
                        "case": test["name"],
                        "status": "PASS",
                        "anomalies": anomaly_count
                    })
                else:
                    print(f"    ✗ Failed with status {response.status_code}")
                    self.results.append({
                        "test": "anomaly_detection",
                        "case": test["name"],
                        "status": "FAIL"
                    })

            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.results.append({
                    "test": "anomaly_detection",
                    "case": test["name"],
                    "status": "ERROR",
                    "error": str(e)
                })

    def test_forecasting(self):
        """Test Time Series Forecasting"""
        print("\n" + "="*70)
        print("TEST: Time Series Forecasting")
        print("="*70)

        models = ["arima", "exponential_smoothing", "linear_trend"]

        for model in models:
            print(f"\n  → Testing {model.upper()} model")

            payload = {
                "tag_id": "SILO_01_NIVEL",
                "horizon": "24h",
                "model": model,
                "confidence_interval": 0.95
            }

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ai-insights/forecast",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    predictions = data.get("predictions", [])
                    metrics = data.get("metrics", {})

                    print(f"    ✓ Predictions generated: {len(predictions)} points")
                    print(f"    ✓ MAE: {metrics.get('mae', 'N/A')}")
                    print(f"    ✓ RMSE: {metrics.get('rmse', 'N/A')}")
                    print(f"    ✓ R²: {metrics.get('r2', 'N/A')}")

                    # Check prediction quality
                    if predictions:
                        first = predictions[0]
                        print(f"    ✓ First prediction:")
                        print(f"      - Value: {first.get('value')}")
                        print(f"      - Lower bound: {first.get('lower')}")
                        print(f"      - Upper bound: {first.get('upper')}")

                    self.results.append({
                        "test": "forecasting",
                        "model": model,
                        "status": "PASS",
                        "predictions": len(predictions)
                    })
                else:
                    print(f"    ✗ Failed with status {response.status_code}")

            except Exception as e:
                print(f"    ✗ Error: {e}")

    def test_pattern_recognition(self):
        """Test Pattern Recognition"""
        print("\n" + "="*70)
        print("TEST: Pattern Recognition & Correlation Analysis")
        print("="*70)

        patterns = [
            {
                "name": "Speed-Current Correlation",
                "tag_ids": ["CORREIA_01_VELOCIDADE", "CORREIA_01_CORRENTE"],
                "pattern_type": "correlation",
                "expected": "positive correlation"
            },
            {
                "name": "Temperature-Level Pattern",
                "tag_ids": ["SILO_01_TEMPERATURA", "SILO_01_NIVEL"],
                "pattern_type": "seasonal",
                "expected": "seasonal pattern"
            }
        ]

        for pattern in patterns:
            print(f"\n  → {pattern['name']}")

            payload = {
                "tag_ids": pattern["tag_ids"],
                "duration": "7d",
                "pattern_type": pattern["pattern_type"]
            }

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ai-insights/find-patterns",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    patterns_found = data.get("patterns", [])
                    print(f"    ✓ Patterns found: {len(patterns_found)}")

                    if pattern["pattern_type"] == "correlation":
                        correlation = data.get("correlation_coefficient", 0)
                        print(f"    ✓ Correlation: {correlation:.3f}")

                    for p in patterns_found[:3]:
                        print(f"    ✓ Pattern: {p.get('type')} - {p.get('description')}")

                    self.results.append({
                        "test": "pattern_recognition",
                        "case": pattern["name"],
                        "status": "PASS",
                        "patterns": len(patterns_found)
                    })
                else:
                    print(f"    ✗ Failed with status {response.status_code}")

            except Exception as e:
                print(f"    ✗ Error: {e}")

    def test_predictive_maintenance(self):
        """Test Predictive Maintenance Scoring"""
        print("\n" + "="*70)
        print("TEST: Predictive Maintenance Scoring")
        print("="*70)

        equipment_list = [
            {
                "id": "CORREIA_01",
                "features": ["velocidade", "corrente", "temperatura", "vibracao"],
                "expected_score": "> 70"
            },
            {
                "id": "PORTA_01",
                "features": ["posicao", "corrente", "ciclos", "tempo_resposta"],
                "expected_score": "> 80"
            }
        ]

        for equipment in equipment_list:
            print(f"\n  → Equipment: {equipment['id']}")

            payload = {
                "equipment_id": equipment["id"],
                "features": equipment["features"],
                "duration": "30d"
            }

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/ai-insights/maintenance-score",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    health_score = data.get("health_score", 0)
                    risk_level = data.get("risk_level", "unknown")
                    recommendations = data.get("recommendations", [])

                    print(f"    ✓ Health Score: {health_score}/100")
                    print(f"    ✓ Risk Level: {risk_level}")
                    print(f"    ✓ Recommendations: {len(recommendations)}")

                    # Feature importance
                    if "feature_importance" in data:
                        print(f"    ✓ Feature Importance:")
                        for feature, importance in data["feature_importance"].items():
                            print(f"      - {feature}: {importance:.2f}")

                    # Predicted issues
                    if "predicted_issues" in data:
                        print(f"    ✓ Predicted Issues:")
                        for issue in data["predicted_issues"]:
                            print(f"      - {issue}")

                    self.results.append({
                        "test": "predictive_maintenance",
                        "equipment": equipment["id"],
                        "status": "PASS",
                        "health_score": health_score
                    })
                else:
                    print(f"    ✗ Failed with status {response.status_code}")

            except Exception as e:
                print(f"    ✗ Error: {e}")

    def test_advanced_analytics(self):
        """Test Advanced Analytics Capabilities"""
        print("\n" + "="*70)
        print("TEST: Advanced Analytics")
        print("="*70)

        analytics_tests = [
            {
                "name": "Root Cause Analysis",
                "endpoint": "/api/v1/ai-insights/root-cause",
                "payload": {
                    "event_id": "ALARM_CORREIA_01_ALTA_TEMP",
                    "look_back": "1h",
                    "related_tags": ["CORREIA_01_VELOCIDADE", "CORREIA_01_CORRENTE"]
                }
            },
            {
                "name": "Process Optimization Suggestions",
                "endpoint": "/api/v1/ai-insights/optimize",
                "payload": {
                    "process_id": "GRAIN_RECEPTION",
                    "objective": "maximize_throughput",
                    "constraints": {"energy_budget": 1000}
                }
            },
            {
                "name": "Batch Analysis",
                "endpoint": "/api/v1/ai-insights/batch-analysis",
                "payload": {
                    "batch_id": "BATCH_2024_001",
                    "metrics": ["quality", "efficiency", "waste"]
                }
            }
        ]

        for test in analytics_tests:
            print(f"\n  → {test['name']}")

            try:
                response = requests.post(
                    f"{self.base_url}{test['endpoint']}",
                    json=test["payload"],
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✓ Analysis completed")
                    print(f"    ✓ Results: {json.dumps(data, indent=2)[:200]}...")

                    self.results.append({
                        "test": "advanced_analytics",
                        "case": test["name"],
                        "status": "PASS"
                    })
                else:
                    print(f"    ✗ Failed with status {response.status_code}")

            except Exception as e:
                print(f"    ✗ Error: {e}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("MACHINE LEARNING TEST REPORT")
        print("="*70)

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.results if r["status"] == "ERROR"])

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")

        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")

        # Save detailed results
        with open(f"{RESULTS_DIR}/ml_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "errors": error_tests,
                    "success_rate": success_rate if total_tests > 0 else 0
                },
                "results": self.results
            }, f, indent=2)

        print(f"\n✓ Detailed results saved to {RESULTS_DIR}/")

        return passed_tests == total_tests

def main():
    """Main test execution"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     OptiFlow AI - Machine Learning Test Suite              ║
║     Branch: fix-autonomous-agent-sessions                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

    tester = MLTester()

    # Run all tests
    tester.test_anomaly_detection()
    tester.test_forecasting()
    tester.test_pattern_recognition()
    tester.test_predictive_maintenance()
    tester.test_advanced_analytics()

    # Generate report
    success = tester.generate_report()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
