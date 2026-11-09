"""
Weather Impact & Safety Regulation Engine for Where Is My Train
Evaluates adverse weather conditions and speed restrictions across Indian Railways divisions
using real-time Open-Meteo live meteorology API and G&SR safety standards.
"""

import json
import logging
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("WeatherSafetyEngine")


@dataclass
class WeatherCondition:
    condition_name: str
    speed_cap_kmh: float
    safety_protocol: str
    penalty_multiplier: float
    is_adverse: bool
    risk_level: str
    source: str = "IR Safety Manual Fallback"
    visibility_meters: Optional[float] = None
    temperature_celsius: Optional[float] = None
    precipitation_mm: Optional[float] = None
    weather_code: Optional[int] = None


class OpenMeteoClient:
    """Live weather ingestion client via the Open-Meteo API with caching and error isolation."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_TTL_SECONDS = 900.0  # 15 minutes cache per coordinate grid

    # In-memory coordinate cache: (lat_rounded, lng_rounded) -> (expire_timestamp, data_dict)
    _cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}

    @classmethod
    def batch_prefetch_weather(cls, coordinates: List[Tuple[float, float]], timeout_seconds: float = 4.0) -> None:
        """Prefetches live weather for a list of coordinates in a single batched HTTP request."""
        now = time.time()
        uncached: List[Tuple[float, float]] = []

        for lat, lng in coordinates:
            k = (round(float(lat), 3), round(float(lng), 3))
            if k not in cls._cache or now >= cls._cache[k][0]:
                if k not in uncached:
                    uncached.append(k)

        if not uncached:
            return

        # Chunk in groups of up to 50 coordinates per Open-Meteo guidelines
        for i in range(0, len(uncached), 45):
            chunk = uncached[i:i + 45]
            lats = ",".join(f"{c[0]:.3f}" for c in chunk)
            lngs = ",".join(f"{c[1]:.3f}" for c in chunk)
            url = (
                f"{cls.BASE_URL}?latitude={lats}&longitude={lngs}"
                f"&current=temperature_2m,precipitation,visibility,weather_code"
            )
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "GatiSetu-RailEngine/2.0 (IndianRailways-Research)"}
                )
                with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                    if resp.status == 200:
                        raw = json.loads(resp.read().decode("utf-8"))
                        if isinstance(raw, list):
                            for idx, item in enumerate(raw):
                                cur = item.get("current", {})
                                cls._cache[chunk[idx]] = (now + cls.CACHE_TTL_SECONDS, cur)
                        elif isinstance(raw, dict) and len(chunk) == 1:
                            cls._cache[chunk[0]] = (now + cls.CACHE_TTL_SECONDS, raw.get("current", {}))
            except Exception as e:
                logger.warning(f"Batch Open-Meteo prefetch failed: {e}")

    @classmethod
    def get_live_weather(cls, latitude: float, longitude: float, timeout_seconds: float = 3.5) -> Optional[Dict[str, Any]]:
        """Queries Open-Meteo for live visibility, temperature, precipitation, and weather code."""
        lat_key = round(float(latitude), 3)
        lng_key = round(float(longitude), 3)
        now = time.time()

        # Check cache
        if (lat_key, lng_key) in cls._cache:
            expires_at, cached_data = cls._cache[(lat_key, lng_key)]
            if now < expires_at:
                return cached_data

        url = (
            f"{cls.BASE_URL}?latitude={lat_key}&longitude={lng_key}"
            f"&current=temperature_2m,precipitation,visibility,weather_code"
        )

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "GatiSetu-RailEngine/2.0 (IndianRailways-Research)"}
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                if resp.status == 200:
                    raw = json.loads(resp.read().decode("utf-8"))
                    current = raw.get("current", {})
                    cls._cache[(lat_key, lng_key)] = (now + cls.CACHE_TTL_SECONDS, current)
                    return current
        except Exception as e:
            logger.warning(f"Open-Meteo live weather query failed for ({lat_key}, {lng_key}): {e}")

        return None


class WeatherSafetyEngine:
    """
    Evaluates real-time weather against Indian Railways General & Subsidiary Rules (G&SR)
    speed restriction protocols.
    """

    # Division-level adverse weather zones (Fallback when offline or station coordinates unavailable)
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

    # Station coordinates fallback cache for key junctions
    PRESET_COORDINATES: Dict[str, Tuple[float, float]] = {
        "NDLS": (28.6418, 77.2203),
        "CNB": (26.4539, 80.3513),
        "PRYJ": (25.4439, 81.8267),
        "DDU": (25.2796, 83.1232),
        "MMCT": (18.9708, 72.8194),
        "BAP": (19.6200, 74.6599),
        "KPG": (19.9036, 74.5036),
        "MMR": (20.2526, 74.5262),
        "BSL": (21.0478, 75.7878),
        "RTM": (23.3394, 75.0494),
        "NAD": (23.4562, 75.4125),
        "KOTA": (25.2185, 75.8647),
        "HWH": (22.5838, 88.3422),
    }

    _asset_db_instance: Any = None

    @classmethod
    def get_coordinates_for_station(cls, station_code: str) -> Optional[Tuple[float, float]]:
        """Resolves GPS coordinates for any Indian station from cache or WIMT SQLite asset database."""
        stn = str(station_code or "").upper().strip()
        if stn in cls.PRESET_COORDINATES:
            return cls.PRESET_COORDINATES[stn]

        try:
            if cls._asset_db_instance is None:
                from .asset_database import WIMTAssetDatabase
                cls._asset_db_instance = WIMTAssetDatabase()
            info = cls._asset_db_instance.get_station_info(stn)
            if info and info.get("latitude") and info.get("longitude"):
                coords = (float(info["latitude"]), float(info["longitude"]))
                cls.PRESET_COORDINATES[stn] = coords
                return coords
        except Exception:
            pass
        return None

    @classmethod
    def evaluate_station_weather(
        cls,
        station_code: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> WeatherCondition:
        """
        Determines localized weather conditions and safety speed restrictions for a station
        using live Open-Meteo telemetry with automatic G&SR safety fallback.
        """
        stn = str(station_code or "").upper().strip()

        # Resolve coordinates if not provided
        lat = latitude
        lng = longitude
        if lat is None or lng is None:
            coords = cls.get_coordinates_for_station(stn)
            if coords:
                lat, lng = coords

        # 1. Query Open-Meteo Live API if coordinates are known
        if lat is not None and lng is not None:
            live = OpenMeteoClient.get_live_weather(lat, lng)
            if live:
                vis_m = float(live.get("visibility") or 10000.0)
                temp_c = float(live.get("temperature_2m") or 25.0)
                precip_mm = float(live.get("precipitation") or 0.0)
                w_code = int(live.get("weather_code") or 0)

                # Rule A: Dense Fog (Visibility < 150m or WMO 45/48 dense fog)
                if vis_m < 150.0 or (w_code in (45, 48) and vis_m < 800.0):
                    return WeatherCondition(
                        condition_name=f"Live Dense Fog (Visibility {int(vis_m)}m)",
                        speed_cap_kmh=60.0,
                        safety_protocol="FOG-PASS Device Protection (Max 60 km/h)",
                        penalty_multiplier=1.45,
                        is_adverse=True,
                        risk_level="CRITICAL",
                        source="Open-Meteo Live API",
                        visibility_meters=vis_m,
                        temperature_celsius=temp_c,
                        precipitation_mm=precip_mm,
                        weather_code=w_code
                    )

                # Rule B: Moderate Fog / Mist (Visibility 150m - 500m)
                if vis_m < 500.0:
                    return WeatherCondition(
                        condition_name=f"Live Moderate Fog (Visibility {int(vis_m)}m)",
                        speed_cap_kmh=75.0,
                        safety_protocol="FOG-PASS Caution Order (Max 75 km/h)",
                        penalty_multiplier=1.25,
                        is_adverse=True,
                        risk_level="HIGH",
                        source="Open-Meteo Live API",
                        visibility_meters=vis_m,
                        temperature_celsius=temp_c,
                        precipitation_mm=precip_mm,
                        weather_code=w_code
                    )

                # Rule C: Torrential Monsoon Rain / Waterlogging (Precipitation >= 25 mm/h or Storm)
                if precip_mm >= 25.0 or w_code in (65, 82, 95, 96, 99):
                    return WeatherCondition(
                        condition_name=f"Live Monsoon Storm ({precip_mm} mm/h)",
                        speed_cap_kmh=45.0,
                        safety_protocol="Track Waterlogging Caution Order (Max 45 km/h)",
                        penalty_multiplier=1.40,
                        is_adverse=True,
                        risk_level="CRITICAL",
                        source="Open-Meteo Live API",
                        visibility_meters=vis_m,
                        temperature_celsius=temp_c,
                        precipitation_mm=precip_mm,
                        weather_code=w_code
                    )

                # Rule D: Heavy Rain & Adhesion Caution (Precipitation >= 10 mm/h)
                if precip_mm >= 10.0 or w_code in (63, 81):
                    return WeatherCondition(
                        condition_name=f"Live Heavy Rain ({precip_mm} mm/h)",
                        speed_cap_kmh=65.0,
                        safety_protocol="Rail Adhesion & Braking Distance Buffer (Max 65 km/h)",
                        penalty_multiplier=1.20,
                        is_adverse=True,
                        risk_level="HIGH",
                        source="Open-Meteo Live API",
                        visibility_meters=vis_m,
                        temperature_celsius=temp_c,
                        precipitation_mm=precip_mm,
                        weather_code=w_code
                    )

                # Rule E: Extreme Heat Wave & Rail Buckling (> 43°C)
                if temp_c >= 43.0:
                    return WeatherCondition(
                        condition_name=f"Live Extreme Heat ({temp_c}°C - Sun-Kink TSR)",
                        speed_cap_kmh=100.0,
                        safety_protocol="Continuous Welded Rail Heat TSR (Max 100 km/h)",
                        penalty_multiplier=1.15,
                        is_adverse=True,
                        risk_level="MODERATE",
                        source="Open-Meteo Live API",
                        visibility_meters=vis_m,
                        temperature_celsius=temp_c,
                        precipitation_mm=precip_mm,
                        weather_code=w_code
                    )

                # Rule F: Clear / Standard Track Operations
                return WeatherCondition(
                    condition_name=f"Clear Weather ({temp_c}°C, Vis {int(vis_m / 1000)}km)",
                    speed_cap_kmh=130.0,
                    safety_protocol="Standard Section MPS",
                    penalty_multiplier=1.0,
                    is_adverse=False,
                    risk_level="LOW",
                    source="Open-Meteo Live API",
                    visibility_meters=vis_m,
                    temperature_celsius=temp_c,
                    precipitation_mm=precip_mm,
                    weather_code=w_code
                )

        # 2. Regional Division Fallback if coordinates missing or Open-Meteo unreachable
        for key, zone in cls.REGIONAL_ZONES.items():
            if stn in zone["stations"]:
                return WeatherCondition(
                    condition_name=zone["name"],
                    speed_cap_kmh=zone["speed_cap_kmh"],
                    safety_protocol=zone["safety_protocol"],
                    penalty_multiplier=zone["penalty_multiplier"],
                    is_adverse=True,
                    risk_level=zone["risk_level"],
                    source="IR Safety Manual Fallback"
                )

        return WeatherCondition(
            condition_name="Clear / Standard Track Operations",
            speed_cap_kmh=130.0,
            safety_protocol="Standard Section MPS",
            penalty_multiplier=1.0,
            is_adverse=False,
            risk_level="LOW",
            source="Default Clear Section"
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
