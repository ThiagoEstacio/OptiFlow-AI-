#!/usr/bin/env python3
"""
Update Performance Dashboard with Real-time Metrics
Automatically updates PERFORMANCE_DASHBOARD.md with current system metrics
"""

import json
import requests
import datetime
from pathlib import Path


class DashboardUpdater:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.dashboard_path = Path(__file__).parent.parent / "docs" / "PERFORMANCE_DASHBOARD.md"
        
    def get_current_metrics(self):
        """Fetch current metrics from backend"""
        try:
            # ML model status
            ml_response = requests.get(f"{self.backend_url}/api/v1/analytics/model-info", timeout=5)
            ml_data = ml_response.json() if ml_response.status_code == 200 else {}
            
            # System health
            health_response = requests.get(f"{self.backend_url}/health", timeout=5)
            health_data = health_response.json() if health_response.status_code == 200 else {}
            
            return {
                "ml_f1_score": ml_data.get("metrics", {}).get("f1_score", 0.1032),
                "ml_precision": ml_data.get("metrics", {}).get("precision", 0.05),
                "ml_recall": ml_data.get("metrics", {}).get("recall", 0.5),
                "system_status": health_data.get("status", "unknown"),
                "api_latency": 500,  # TODO: Implement latency tracking
                "uptime": 95.0,      # TODO: Implement uptime tracking
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️  Could not fetch metrics: {e}")
            return None
    
    def calculate_progress_bar(self, current, target, length=30):
        """Generate progress bar string"""
        percentage = min(100, (current / target) * 100)
        filled = int((percentage / 100) * length)
        return "█" * filled + "░" * (length - filled)
    
    def calculate_health_score(self, metrics):
        """Calculate overall health score based on metrics"""
        if not metrics:
            return 65  # Default
        
        # Weighted scoring
        scores = {
            "performance": min(100, (metrics["ml_f1_score"] / 0.42) * 100),
            "scalability": 40,  # Static for now
            "reliability": min(100, (metrics["uptime"] / 99.9) * 100),
            "maintainability": 35,  # Static
            "security": 60  # Static
        }
        
        # Weighted average
        overall = (
            scores["performance"] * 0.25 +
            scores["scalability"] * 0.25 +
            scores["reliability"] * 0.20 +
            scores["maintainability"] * 0.20 +
            scores["security"] * 0.10
        )
        
        return {
            "overall": int(overall),
            **scores
        }
    
    def update_dashboard(self, metrics, scores):
        """Update dashboard markdown file with new metrics"""
        if not self.dashboard_path.exists():
            print(f"❌ Dashboard not found at {self.dashboard_path}")
            return False
        
        content = self.dashboard_path.read_text()
        
        # Update timestamp
        now = datetime.datetime.now().strftime("%d de %B de %Y")
        content = content.replace(
            "**Última Atualização:** 11 de Novembro de 2025",
            f"**Última Atualização:** {now}"
        )
        
        # Update health scores
        overall_bar = self.calculate_progress_bar(scores["overall"], 100, 10)
        content = content.replace(
            "Overall Score:  ████████░░  65/100",
            f"Overall Score:  {overall_bar}  {scores['overall']}/100"
        )
        
        # Update ML F1-Score
        f1_current = metrics["ml_f1_score"]
        f1_bar_current = self.calculate_progress_bar(f1_current, 0.42, 30)
        content = content.replace(
            "ML F1-Score\nCurrent:  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.1032",
            f"ML F1-Score\nCurrent:  {f1_bar_current}  {f1_current:.4f}"
        )
        
        # Update uptime
        uptime_bar = self.calculate_progress_bar(metrics["uptime"], 99.9, 30)
        content = content.replace(
            "Uptime\nCurrent:  ███████████████████████████░░░░░  95%",
            f"Uptime\nCurrent:  {uptime_bar}  {metrics['uptime']:.1f}%"
        )
        
        # Save updated content
        self.dashboard_path.write_text(content)
        print(f"✅ Dashboard updated successfully!")
        print(f"📊 Overall Health: {scores['overall']}/100")
        print(f"🤖 ML F1-Score: {f1_current:.4f}")
        print(f"⏱️  Uptime: {metrics['uptime']:.1f}%")
        
        return True
    
    def run(self):
        """Main execution"""
        print("🔄 Fetching current metrics...")
        metrics = self.get_current_metrics()
        
        if not metrics:
            print("⚠️  Using default metrics")
            metrics = {
                "ml_f1_score": 0.1032,
                "ml_precision": 0.05,
                "ml_recall": 0.5,
                "system_status": "healthy",
                "api_latency": 500,
                "uptime": 95.0,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        print("📊 Calculating health scores...")
        scores = self.calculate_health_score(metrics)
        
        print("📝 Updating dashboard...")
        success = self.update_dashboard(metrics, scores)
        
        if success:
            print(f"\n✅ Dashboard updated: {self.dashboard_path}")
            print(f"🔗 View at: file://{self.dashboard_path.absolute()}")
        
        return success


if __name__ == "__main__":
    updater = DashboardUpdater()
    updater.run()
