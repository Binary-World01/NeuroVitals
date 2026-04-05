"""
Community Health Intelligence - Outbreak detection
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import Counter


class CommunityHealthService:
    """Community health intelligence and outbreak detection"""
    
    def __init__(self):
        self.mock_reports = self._generate_mock_data()
    
    def _generate_mock_data(self) -> List[dict]:
        """Generate mock health reports for demo"""
        symptoms = ["fever", "cough", "headache", "sore throat", "fatigue", "body ache"]
        areas = [
            {"name": "Andheri West", "lat": 19.1136, "lon": 72.8697},
            {"name": "Bandra East", "lat": 19.0596, "lon": 72.8295},
            {"name": "Dadar", "lat": 19.0178, "lon": 72.8478},
            {"name": "Powai", "lat": 19.1176, "lon": 72.9060},
            {"name": "Colaba", "lat": 18.9067, "lon": 72.8147},
        ]
        
        reports = []
        for area in areas:
            # Create outbreak simulation in some areas
            is_outbreak = random.random() > 0.6
            report_count = random.randint(80, 250) if is_outbreak else random.randint(10, 40)
            
            for _ in range(report_count):
                reports.append({
                    "area": area["name"],
                    "lat": area["lat"] + random.uniform(-0.02, 0.02),
                    "lon": area["lon"] + random.uniform(-0.02, 0.02),
                    "symptoms": random.sample(symptoms, random.randint(2, 4)),
                    "timestamp": datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
                    "severity": random.randint(3, 9)
                })
        
        return reports
    
    def get_heatmap_data(self) -> Dict[str, Any]:
        """Get community health heatmap data"""
        reports = self.mock_reports
        now = datetime.utcnow()
        
        # Time-based filtering
        recent_24h = [r for r in reports if r["timestamp"] > now - timedelta(hours=24)]
        previous_24h = [r for r in reports if now - timedelta(hours=48) < r["timestamp"] <= now - timedelta(hours=24)]
        
        # Calculate transmission velocity
        velocity = ((len(recent_24h) - len(previous_24h)) / max(len(previous_24h), 1)) * 100
        
        # Area aggregation
        area_counts = Counter([r["area"] for r in reports])
        
        # Trending symptoms
        all_symptoms = [s for r in reports for s in r["symptoms"]]
        trending = Counter(all_symptoms).most_common(5)
        
        return {
            "total_reports": len(reports),
            "recent_24h": len(recent_24h),
            "transmission_velocity": round(velocity, 1),
            "trending_symptoms": [{"symptom": s, "count": c} for s, c in trending],
            "area_data": [
                {
                    "area": area,
                    "count": count,
                    "severity": "high" if count > 100 else "medium" if count > 50 else "low"
                }
                for area, count in area_counts.most_common()
            ],
            "map_points": [
                {
                    "lat": r["lat"],
                    "lon": r["lon"],
                    "severity": r["severity"],
                    "symptoms": r["symptoms"]
                }
                for r in recent_24h
            ],
            "outbreak_detected": velocity > 20,
            "alert_message": f"⚠️ Outbreak Alert: Transmission velocity increased by {round(velocity, 1)}% in last 24 hours" if velocity > 20 else None
        }


community_service = CommunityHealthService()
