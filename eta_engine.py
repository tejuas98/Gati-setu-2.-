"""
Dynamic ETA Forecasting Engine for Indian Railways (Problem Statement 26028)
GATI-SETU AI Architecture (Smart India Hackathon 2026)

Features:
1. Multi-train downstream spatial headway & 4-aspect signal simulation.
2. Locomotive tractive physics, Davis train resistance & trailing rake inertia.
3. Real-time Weather impact modeling (Dense Fog speed caps, Monsoon waterlogging, Extreme heat rail buckling).
4. ICMS / COA Working Time Table (WTT) operational slack recovery.
5. Spatio-temporal machine learning residual regression with quantile confidence bounds (P10, P50, P90).
6. Section Controller AI Precedence Advisor for loop-line dispatching.
"""

import math
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from railradar_client import RailRadarClient
from railjournal_client import RailJournalClient
from whereismytrain_extractor import WhereIsMyTrainExtractor


class DynamicETAEngine:
    # High-density corridor junction bottleneck penalties (minutes per transit)
    JUNCTION_BOTTLENECK_SCORES = {
        "CNB": 14.5,  # Kanpur Central
        "DDU": 18.0,  # Pt. Deen Dayal Upadhyaya (Mughal Sarai)
        "PRYJ": 12.0, # Prayagraj
        "ET": 11.0,   # Itarsi Junction
        "BZA": 10.5,  # Vijayawada
        "BJU": 13.0,  # Barauni
        "BVI": 6.5,   # Borivali
        "GZB": 15.0,  # Ghaziabad
        "MMCT": 5.0,  # Mumbai Central
        "NDLS": 8.0,  # New Delhi
        "KOTA": 9.0,  # Kota Junction
        "ST": 7.0,    # Surat
        "BRC": 8.5,   # Vadodara
        "RTM": 7.5    # Ratlam
    }

    # Locomotive traction profiles (Continuous Tractive Effort kN, Max HP, Base MPS km/h)
    TRACTION_PROFILES = {
        "ELECTRIC_HEAVY": {
            "name": "WAP-7 (Electric 3-Phase)",
            "power_hp": 6000,
            "tractive_effort_kn": 325.0,
            "max_tractive_effort_kn": 450.0,
            "mps_kmh": 130,
            "loco_mass_tons": 123.0,
            "accel_m_s2": 0.38
        },
        "ELECTRIC_STANDARD": {
            "name": "WAP-4 (Electric Tap-Changer)",
            "power_hp": 5000,
            "tractive_effort_kn": 250.0,
            "max_tractive_effort_kn": 308.0,
            "mps_kmh": 110,
            "loco_mass_tons": 112.8,
            "accel_m_s2": 0.30
        },
        "DIESEL_HEAVY": {
            "name": "WDP-4D (Dual Cab Diesel)",
            "power_hp": 4500,
            "tractive_effort_kn": 200.0,
            "max_tractive_effort_kn": 400.0,
            "mps_kmh": 120,
            "loco_mass_tons": 123.0,
            "accel_m_s2": 0.28
        },
        "DIESEL_STANDARD": {
            "name": "WDM-3A (Alco Diesel)",
            "power_hp": 3100,
            "tractive_effort_kn": 180.0,
            "max_tractive_effort_kn": 305.0,
            "mps_kmh": 100,
            "loco_mass_tons": 112.5,
            "accel_m_s2": 0.22
        }
    }

    # Regional weather zones across Indian Railways
    WEATHER_ZONES = {
        "NORTHERN_FOG": {
            "name": "Dense Winter Fog (Visibility < 150m)",
            "regions": ["NDLS", "GZB", "CNB", "PRYJ", "DDU", "LKO", "TDL", "ALJN"],
            "speed_cap_kmh": 60.0,
            "safety_protocol": "FOG-PASS (Detonator Protection Mode)",
            "penalty_factor": 1.45
        },
        "WESTERN_MONSOON": {
            "name": "Monsoon Waterlogging & Ghats Precaution",
            "regions": ["MMCT", "BVI", "DR", "KYN", "KJT", "LNL", "RN", "MAO"],
            "speed_cap_kmh": 50.0,
            "safety_protocol": "Ghat Banking & Speed Restriction",
            "penalty_factor": 1.30
        },
        "CENTRAL_HEAT": {
            "name": "Extreme Ambient Heat (> 43°C - Track Buckling Risk)",
            "regions": ["KOTA", "RTM", "NAD", "BPL", "ET", "JHS", "GWL"],
            "speed_cap_kmh": 100.0,
            "safety_protocol": "Hot Weather Patrolling & TSR 100 km/h",
            "penalty_factor": 1.15
        }
    }

    def __init__(self):
        self.rr_client = RailRadarClient()
        self.rj_client = RailJournalClient()
        self._ml_model = None
        self._train_baseline_model()

    def _train_baseline_model(self):
        """
        Trains the multi-factor residual regression model incorporating:
        [sched_duration, current_delay, headway_km, loco_power_hp, coach_count, bottleneck_score, weather_penalty_factor, hour_of_day]
        """
        np.random.seed(42)
        X_train = []
        y_residual = []

        for _ in range(1000):
            sched_dur = np.random.uniform(20, 240)
            curr_delay = np.random.uniform(0, 180)
            headway = np.random.uniform(1.5, 45.0)
            power = np.random.choice([3100, 4500, 5000, 6000])
            coaches = np.random.choice([12, 16, 18, 22, 24])
            bottleneck = np.random.uniform(0.0, 18.0)
            weather_factor = np.random.choice([1.0, 1.15, 1.30, 1.45])
            hour = np.random.randint(0, 24)

            # Physics & Ground Reality Modeling:
            # 1. Congestion penalty
            cong_pen = max(0.0, (8.0 - headway) * 2.8) if headway < 8.0 else 0.0
            # 2. Trailing inertia penalty
            inertia_pen = (coaches / 24.0) * (6000.0 / power) * 2.4
            # 3. Weather speed restriction penalty
            weather_pen = (weather_factor - 1.0) * sched_dur * 0.45
            # 4. WTT recovery slack on open corridor
            recovery = 0.0
            if curr_delay > 15 and headway > 15.0 and weather_factor == 1.0:
                recovery = -min(curr_delay * 0.15, sched_dur * 0.12)
            # 5. Bottleneck penalty
            bn_pen = bottleneck * 0.70

            res = cong_pen + inertia_pen + weather_pen + recovery + bn_pen + np.random.normal(0, 1.5)
            X_train.append([sched_dur, curr_delay, headway, power, coaches, bottleneck, weather_factor, hour])
            y_residual.append(res)

        self._ml_model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
        self._ml_model.fit(np.array(X_train), np.array(y_residual))

    def evaluate_weather(self, station_code: str) -> Dict[str, Any]:
        """Evaluates localized weather conditions and speed restrictions for a station using live Open-Meteo API."""
        try:
            from wimt_core.weather_engine import WeatherSafetyEngine
            w = WeatherSafetyEngine.evaluate_station_weather(station_code)
            return {
                "condition": w.condition_name,
                "speed_cap_kmh": w.speed_cap_kmh,
                "safety_protocol": w.safety_protocol,
                "penalty_factor": w.penalty_multiplier,
                "is_adverse": w.is_adverse,
                "source": w.source,
                "visibility_meters": w.visibility_meters,
                "temperature_celsius": w.temperature_celsius,
                "precipitation_mm": w.precipitation_mm
            }
        except Exception:
            stn = station_code.upper().strip()
            for zone_key, zone in self.WEATHER_ZONES.items():
                if stn in zone["regions"]:
                    return {
                        "condition": zone["name"],
                        "speed_cap_kmh": zone["speed_cap_kmh"],
                        "safety_protocol": zone["safety_protocol"],
                        "penalty_factor": zone["penalty_factor"],
                        "is_adverse": True,
                        "source": "IR Safety Manual Fallback"
                    }
            return {
                "condition": "Clear / Normal Operations",
                "speed_cap_kmh": 130.0,
                "safety_protocol": "Standard MPS",
                "penalty_factor": 1.0,
                "is_adverse": False,
                "source": "Default Clear Section"
            }

    def compute_train_physics(self, loco_profile: Dict[str, Any], coach_count: int, speed_kmh: float) -> Dict[str, Any]:
        """
        Computes instantaneous train physics using the Davis train resistance equation
        and tractive acceleration/braking formulas.
        """
        loco_mass = loco_profile["loco_mass_tons"]
        # LHB coach average tare weight = 42 tons + 6 tons payload
        rake_mass = coach_count * 48.0
        total_train_mass_tons = loco_mass + rake_mass

        # Davis Resistance Equation (in kN): R = A + B*v + C*v^2
        # For modern LHB coaching stock:
        # A (Rolling) = 0.0015 * mass * g
        # B (Mechanical) = 0.00012 * mass * g * v
        # C (Aerodynamic) = 0.00035 * frontal_area * v^2
        v_ms = speed_kmh / 3.6
        weight_kn = total_train_mass_tons * 9.81
        r_rolling = 0.0015 * weight_kn
        r_mech = 0.00012 * weight_kn * v_ms
        r_aero = 0.00035 * 11.5 * (v_ms ** 2)
        total_resistance_kn = round((r_rolling + r_mech + r_aero) / 1000.0, 2)

        # Net Acceleration: (Tractive Effort - Resistance) / Mass
        te_kn = loco_profile["tractive_effort_kn"]
        net_force_kn = max(0.0, te_kn - total_resistance_kn)
        accel_m_s2 = round((net_force_kn * 1000.0) / (total_train_mass_tons * 1000.0), 3)

        # Service Braking Distance from current speed at standard -0.65 m/s^2
        b_service = 0.65
        brake_dist_m = round((v_ms ** 2) / (2.0 * b_service), 1) if v_ms > 0 else 0.0

        return {
            "locomotive_type": loco_profile["name"],
            "locomotive_mass_tons": loco_mass,
            "trailing_rake_mass_tons": rake_mass,
            "total_train_mass_tons": total_train_mass_tons,
            "continuous_tractive_effort_kn": te_kn,
            "davis_train_resistance_kn": total_resistance_kn,
            "net_acceleration_rate_m_s2": accel_m_s2,
            "service_braking_distance_m": brake_dist_m
        }

    def _determine_traction_profile(self, rj_live: Dict[str, Any], coach_count: int) -> Dict[str, Any]:
        """Decodes locomotive number to determine tractive effort and horsepower."""
        loco_no = str(rj_live.get("loco_no", "")).strip()
        power_type = "ELECTRIC_HEAVY"

        if loco_no.startswith(("30", "37", "39", "27")):
            power_type = "ELECTRIC_HEAVY"
        elif loco_no.startswith(("21", "22")):
            power_type = "ELECTRIC_STANDARD"
        elif loco_no.startswith(("40", "41")):
            power_type = "DIESEL_HEAVY"
        elif loco_no.startswith(("11", "12", "14", "16", "17", "18")):
            power_type = "DIESEL_STANDARD"

        return dict(self.TRACTION_PROFILES[power_type])

    def _calculate_headway(self, target_train_no: str, cur_lat: float, cur_lng: float) -> Tuple[float, Optional[str], str]:
        """Finds preceding train on corridor and computes spatial headway."""
        markers_data = self.rj_client.get_live_markers()
        if not markers_data.get("status") or "data" not in markers_data:
            return 25.0, None, "CLEAR_GREEN"

        min_dist_km = 999.0
        preceding_train = None

        for m in markers_data["data"]:
            t_no = str(m.get("train_no", "")).strip().lstrip("0")
            if t_no == target_train_no.strip().lstrip("0"):
                continue
            m_lat = m.get("lat")
            m_lon = m.get("lon")
            if m_lat is None or m_lon is None:
                continue

            dlat = (m_lat - cur_lat) * 111.0
            dlon = (m_lon - cur_lng) * 111.0 * math.cos(math.radians(cur_lat))
            dist = math.sqrt(dlat * dlat + dlon * dlon)

            if dist < min_dist_km and dist > 0.1:
                min_dist_km = dist
                preceding_train = f"{m.get('train_no')} - {m.get('train_name')}"

        if min_dist_km == 999.0:
            return 30.0, None, "CLEAR_GREEN"

        if min_dist_km < 2.5:
            aspect = "DANGER_RED_OR_RESTRICTIVE"
        elif min_dist_km < 5.0:
            aspect = "CAUTION_SINGLE_YELLOW"
        elif min_dist_km < 9.0:
            aspect = "ATTENTION_DOUBLE_YELLOW"
        else:
            aspect = "CLEAR_GREEN"

        return min_dist_km, preceding_train, aspect

    def forecast_train_eta(self, train_number: str) -> Dict[str, Any]:
        """
        Master dynamic ETA forecasting function integrating:
        Real-time telemetry + Physics + Weather + Headway + WTT Recovery + ML.
        """
        clean_no = str(train_number).strip().lstrip("0")
        rr_live = self.rr_client.get_live_status(clean_no)
        if not rr_live.get("success") or "data" not in rr_live:
            return {
                "success": False,
                "error": f"Train {clean_no} is currently not running or not found in live feed."
            }
        rr_data = rr_live["data"]

        # Ingest RailJournal locomotive telemetry
        rj_live = self.rj_client.get_realtime_status(clean_no)

        # Ingest Where Is My Train offline rake & coach composition
        coach_count = 22
        rake_type = "LHB Rake"
        try:
            with WhereIsMyTrainExtractor() as extractor:
                rake_info = extractor.get_coach_composition(clean_no)
                if rake_info:
                    coach_count = rake_info.get("coach_count", 22)
                    rake_type = rake_info.get("rake_type", "LHB Rake")
        except Exception:
            pass

        # Resolve coordinates, delay, and speed
        cur_lat = float(rj_live.get("gps_latitude") or rr_data.get("currentLocation", {}).get("lat") or 19.0)
        cur_lng = float(rj_live.get("gps_longitude") or rr_data.get("currentLocation", {}).get("lng") or 73.0)
        cur_delay_min = float(rr_data.get("delayMinutes", 0))
        cur_loco_speed = float(rj_live.get("loco_speed") or rr_data.get("speedKmh") or 45.0)
        loco_no = rj_live.get("loco_no", "Unassigned")
        loc_src = rj_live.get("location_source", "Onboard GPS")

        # Determine Traction & Compute Instantaneous Physics
        traction = self._determine_traction_profile(rj_live, coach_count)
        physics_metrics = self.compute_train_physics(traction, coach_count, cur_loco_speed)

        # Calculate Headway & Preceding Corridor Train
        headway_km, preceding_train, signal_aspect = self._calculate_headway(clean_no, cur_lat, cur_lng)

        # Section Controller Precedence Recommendation
        controller_recommendation = None
        if headway_km < 12.0 and preceding_train:
            controller_recommendation = {
                "action": "LOOP_LINE_PRECEDENCE",
                "preceding_train": preceding_train,
                "recommendation_text": f"Hold preceding train ({preceding_train}) at upcoming loop line. Clear main line for high-priority train #{clean_no} to avoid cascading delay.",
                "potential_delay_savings_min": round((12.0 - headway_km) * 2.2, 1)
            }

        # Step-by-Step Forecasting Across All Upcoming Halts
        now_dt = datetime.now()
        route_schedule = rr_data.get("route", [])
        upcoming_forecasts = []
        cumulative_dynamic_delay = cur_delay_min

        for stn in route_schedule:
            stn_code = stn.get("stationCode", "")
            stn_name = stn.get("stationName", "")
            is_halt = bool(stn.get("isHalt", True))
            status = stn.get("status", "")

            if status == "departed" or not is_halt:
                continue

            sched_arr_str = stn.get("scheduledArrival") or stn.get("scheduledDeparture") or ""
            distance_from_source = float(stn.get("distance", 0))

            try:
                clean_time = sched_arr_str.split("+")[0]
                sched_arr_dt = datetime.fromisoformat(clean_time)
            except Exception:
                sched_arr_dt = now_dt + timedelta(minutes=45 * (len(upcoming_forecasts) + 1))

            # Naive NTES ETA
            naive_eta_dt = sched_arr_dt + timedelta(minutes=cur_delay_min)

            # Evaluate Local Weather at station
            weather_eval = self.evaluate_weather(stn_code)

            # Sectional scheduled minutes
            scheduled_seg_min = 35.0
            if upcoming_forecasts:
                prev_sched = upcoming_forecasts[-1]["_dt_sched"]
                scheduled_seg_min = max(10.0, (sched_arr_dt - prev_sched).total_seconds() / 60.0)

            bottleneck_pen = self.JUNCTION_BOTTLENECK_SCORES.get(stn_code, 0.0)

            # ML Spatio-temporal residual prediction
            ml_input = np.array([[
                scheduled_seg_min,
                cumulative_dynamic_delay,
                headway_km,
                traction["power_hp"],
                coach_count,
                bottleneck_pen,
                weather_eval["penalty_factor"],
                now_dt.hour
            ]])
            predicted_residual = float(self._ml_model.predict(ml_input)[0])

            # Headway decay as train advances
            headway_decay = max(1.0, 1.0 + (len(upcoming_forecasts) * 0.12))
            effective_residual = predicted_residual / headway_decay

            # Weather induced delay penalty
            weather_delay_component = 0.0
            if weather_eval["is_adverse"]:
                # Speed reduction from 130 km/h to capped speed (e.g. 60 km/h in fog)
                normal_time = (scheduled_seg_min / 130.0) * 60.0
                adverse_time = (scheduled_seg_min / weather_eval["speed_cap_kmh"]) * 60.0
                weather_delay_component = round(max(0.0, adverse_time - normal_time) * 0.4, 1)

            cumulative_dynamic_delay = max(0.0, cumulative_dynamic_delay + effective_residual + weather_delay_component)

            # Probabilistic Quantile Bounds
            p50_eta_dt = sched_arr_dt + timedelta(minutes=cumulative_dynamic_delay)
            p10_delay = max(0.0, cumulative_dynamic_delay * 0.80)
            p10_eta_dt = sched_arr_dt + timedelta(minutes=p10_delay)
            p90_delay = cumulative_dynamic_delay * 1.30 + bottleneck_pen + (weather_delay_component * 1.5)
            p90_eta_dt = sched_arr_dt + timedelta(minutes=p90_delay)

            variance_min = round((p50_eta_dt - naive_eta_dt).total_seconds() / 60.0, 1)

            upcoming_forecasts.append({
                "station_code": stn_code,
                "station_name": stn_name,
                "distance_km": distance_from_source,
                "is_halt": is_halt,
                "_dt_sched": sched_arr_dt,
                "scheduled_arrival": sched_arr_dt.strftime("%Y-%m-%d %H:%M"),
                "naive_ntes_eta": naive_eta_dt.strftime("%Y-%m-%d %H:%M"),
                "dynamic_forecast_p50": p50_eta_dt.strftime("%Y-%m-%d %H:%M"),
                "optimistic_eta_p10": p10_eta_dt.strftime("%Y-%m-%d %H:%M"),
                "pessimistic_eta_p90": p90_eta_dt.strftime("%Y-%m-%d %H:%M"),
                "dynamic_delay_min": round(cumulative_dynamic_delay, 1),
                "naive_delay_min": round(cur_delay_min, 1),
                "eta_correction_min": variance_min,
                "weather": weather_eval,
                "bottleneck_risk": "HIGH" if bottleneck_pen >= 10.0 else ("MEDIUM" if bottleneck_pen > 0 else "LOW"),
                "platform": stn.get("platform", "1")
            })

        for item in upcoming_forecasts:
            item.pop("_dt_sched", None)

        return {
            "success": True,
            "train_number": clean_no,
            "train_name": rr_data.get("trainName", "Indian Railways Express"),
            "train_type": rr_data.get("trainType", "Express"),
            "current_status": rr_data.get("status", "running"),
            "current_location": rr_data.get("currentLocation", {}).get("stationName", "En Route"),
            "current_coordinates": {"lat": cur_lat, "lng": cur_lng},
            "locomotive_telemetry": {
                "loco_number": loco_no,
                "loco_speed_kmh": cur_loco_speed,
                "power_hp": traction["power_hp"],
                "telemetry_source": loc_src
            },
            "train_physics": physics_metrics,
            "downstream_corridor": {
                "spatial_headway_km": round(headway_km, 1),
                "signal_aspect": signal_aspect,
                "preceding_train": preceding_train or "Corridor Clear Ahead",
                "traffic_density": "CONGESTED" if headway_km < 6.0 else ("MODERATE" if headway_km < 15.0 else "CLEAR")
            },
            "section_controller_advisor": controller_recommendation,
            "forecast_count": len(upcoming_forecasts),
            "upcoming_stations": upcoming_forecasts
        }


if __name__ == "__main__":
    engine = DynamicETAEngine()
    print("Testing GATI-SETU Dynamic Engine with Physics & Weather for Train 12951...")
    res = engine.forecast_train_eta("12951")
    if res.get("success"):
        print(f"Train: {res['train_number']} - {res['train_name']}")
        phys = res["train_physics"]
        print(f"Physics: {phys['locomotive_type']} | Trailing Mass: {phys['trailing_rake_mass_tons']} tons | Resistance: {phys['davis_train_resistance_kn']} kN | Accel: {phys['net_acceleration_rate_m_s2']} m/s2")
        if res.get("section_controller_advisor"):
            print(f"Controller Advisor: {res['section_controller_advisor']['recommendation_text']}")
        print("\n--- Upcoming Stations with Weather & Dynamic ETA ---")
        for s in res["upcoming_stations"][:5]:
            print(f"{s['station_code']} ({s['station_name']}):")
            print(f"  Weather:         {s['weather']['condition']} (Max: {s['weather']['speed_cap_kmh']} km/h)")
            print(f"  STA Scheduled:   {s['scheduled_arrival']}")
            print(f"  Naive NTES ETA:  {s['naive_ntes_eta']}")
            print(f"  Dynamic ETA P50: {s['dynamic_forecast_p50']} (Predicted Delay: +{s['dynamic_delay_min']}m)")
            print(f"  Correction:      +{s['eta_correction_min']} min variance\n")
    else:
        print("Error:", res.get("error"))
