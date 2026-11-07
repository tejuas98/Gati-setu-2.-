"""
Weather Impact & Safety Regulation Engine for Where Is My Train
Evaluates adverse weather conditions and speed restrictions across Indian Railways divisions.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class WeatherCondition:
    condition_name: str
    speed_cap_kmh: float
    safety_protocol: str
    penalty_multiplier: float
    is_adverse: bool
    risk_level: str


class WeatherSafetyEngine:
    # Division-level adverse weather zones
    REGIONAL_ZONES: Dict[str, Dict[str, Any]] = {
        "NORTHERN_FOG": {
            "name": "Dense Winter Fog (Visibility < 150m)",
            "stations": ["NDLS", "GZB", "CNB", "PRYJ", "DDU", "LKO", "TDL", "ALJN", "MB", "BE", "ASR"],
            "speed_cap_kmh": 60.0,
            "safety_protocol": "FOG-PASS Device Protection (Max 60 km/h)",
            "penalty_multiplier": 1.45,
            "risk_level": "CRITICAL"
        },
        "WESTERN_MONSOON": {
            "name": "Monsoon Waterlogging & Ghats Caution",
            "stations": ["MMCT", "BVI", "DR", "KYN", "KJT", "LNL", "RN", "MAO", "UD", "PNVL"],
            "speed_cap_kmh": 50.0,
            "safety_protocol": "Ghat Banking & Waterlogging Caution (Max 50 km/h)",
            "penalty_multiplier": 1.30,
            "risk_level": "HIGH"
        },
        "CENTRAL_HEAT": {
            "name": "Extreme Heat Wave (> 43°C - Sun-Kink TSR)",
            "stations": ["KOTA", "RTM", "NAD", "BPL", "ET", "JHS", "GWL", "BZA", "NGP", "WR"],
            "speed_cap_kmh": 100.0,
            "safety_protocol": "Track Buckling TSR (Max 100 km/h)",
            "penalty_multiplier": 1.15,
            "risk_level": "MODERATE"
        }
    }

    @classmethod
    def evaluate_station_weather(cls, station_code: str) -> WeatherCondition:
        """Determines localized weather conditions and safety speed restrictions for a station."""
        stn = str(station_code or "").upper().strip()

        for key, zone in cls.REGIONAL_ZONES.items():
            if stn in zone["stations"]:
                return WeatherCondition(
                    condition_name=zone["name"],
                    speed_cap_kmh=zone["speed_cap_kmh"],
                    safety_protocol=zone["safety_protocol"],
                    penalty_multiplier=zone["penalty_multiplier"],
                    is_adverse=True,
                    risk_level=zone["risk_level"]
                )

        return WeatherCondition(
            condition_name="Clear / Standard Track Operations",
            speed_cap_kmh=130.0,
            safety_protocol="Standard Section MPS",
            penalty_multiplier=1.0,
            is_adverse=False,
            risk_level="LOW"
        )

    @classmethod
    def compute_weather_delay_penalty(
        cls,
        weather: WeatherCondition,
        section_distance_km: float,
        scheduled_minutes: float
    ) -> float:
        """
        Calculates the exact delay in minutes introduced by weather speed restrictions.
        Formula: Delta_t = (Dist / Speed_capped - Dist / Speed_scheduled) * 60
        """
        if not weather.is_adverse:
            return 0.0

        scheduled_speed = (section_distance_km / max(1.0, scheduled_minutes)) * 60.0
        capped_speed = min(scheduled_speed, weather.speed_cap_kmh)

        if capped_speed >= scheduled_speed:
            return 0.0

        adverse_minutes = (section_distance_km / capped_speed) * 60.0
        delay_minutes = max(0.0, adverse_minutes - scheduled_minutes)
        return round(delay_minutes, 1)

