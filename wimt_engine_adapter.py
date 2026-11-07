"""
Where Is My Train (WIMT) Machine Learning Dynamic ETA Adapter
Replaces Where Is My Train's naive static delay addition with the GATI-SETU Spatio-Temporal ML Engine.

Compares:
1. OLD WIMT Static Formula: Predicted Arrival = Scheduled Arrival + Current Delay (Static constant)
2. NEW GATI-SETU Dynamic ML Formula: Predicted Arrival = Scheduled Arrival + Dynamic Compounded Delay
   (Headway Simulation + Locomotive Tractive Effort + Trailing Inertia + WTT Slack Recovery + ML Residuals)
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eta_engine import DynamicETAEngine
from whereismytrain_extractor import WhereIsMyTrainExtractor
from railradar_client import RailRadarClient
from railjournal_client import RailJournalClient


class WIMTEngineAdapter:
    def __init__(self):
        self.dynamic_engine = DynamicETAEngine()
        self.rr_client = RailRadarClient()
        self.rj_client = RailJournalClient()

    def get_wimt_native_running_status(self, train_number: str) -> Dict[str, Any]:
        """
        Generates the exact JSON response expected by the Where Is My Train Android client,
        injecting the GATI-SETU Dynamic ML ETA into 'actual_or_predicted_arrival_time'
        and providing side-by-side comparison with the legacy static algorithm.
        """
        clean_no = str(train_number).strip().lstrip("0")
        forecast = self.dynamic_engine.forecast_train_eta(clean_no)
        if not forecast.get("success"):
            return {
                "status": "error",
                "message": forecast.get("error", "Train not currently running.")
            }

        # Extract train metadata from offline WIMT database
        wimt_title = forecast.get("train_name")
        wimt_type = forecast.get("train_type")
        coach_formation = []
        try:
            with WhereIsMyTrainExtractor() as extractor:
                t_info = extractor.search_train(clean_no)
                if t_info:
                    wimt_title = t_info[0].get("train_name", wimt_title)
                    wimt_type = t_info[0].get("train_type", wimt_type)
                rake = extractor.get_coach_composition(clean_no)
                if rake:
                    coach_formation = rake.get("coaches", [])
        except Exception:
            pass

        current_loc = forecast.get("current_location", "En Route")
        cur_coords = forecast.get("current_coordinates", {"lat": 19.0, "lng": 73.0})
        loco_speed = forecast.get("locomotive_telemetry", {}).get("loco_speed_kmh", 0)
        loco_no = forecast.get("locomotive_telemetry", {}).get("loco_number", "Unassigned")

        # Build station-by-station itinerary formatted for WIMT Android App
        legacy_static_stations = []
        dynamic_ml_stations = []

        for stn in forecast.get("upcoming_stations", []):
            stn_code = stn.get("station_code")
            stn_name = stn.get("station_name")
            dist_km = stn.get("distance_km")
            sched_arr = stn.get("scheduled_arrival")
            platform = stn.get("platform", "1")

            # 1. Old WIMT Static Representation
            legacy_static_stations.append({
                "station_code": stn_code,
                "station_name": stn_name,
                "distance_km": dist_km,
                "scheduled_arrival_time": sched_arr,
                "actual_or_predicted_arrival_time": stn.get("naive_ntes_eta"),
                "delay_minutes": stn.get("naive_delay_min"),
                "prediction_algorithm": "LEGACY_STATIC_SCHEDULE_OFFSET",
                "platform": platform,
                "delay_status": "ON_TIME" if stn.get("naive_delay_min") <= 0 else "DELAYED"
            })

            # Standard WIMT Android App field: 'actual_or_predicted_arrival_time'
            # REPLACED: Old static formula (STA + current_delay) has been removed.
            # INJECTED: GATI-SETU Dynamic Formula (STA + Dynamic Compounded Delay incorporating weather + traction physics)
            dynamic_arrival = stn.get("dynamic_forecast_p50")
            dynamic_delay = stn.get("dynamic_delay_min")
            weather_desc = stn.get("weather_condition", "Clear")
            speed_cap = stn.get("weather_speed_cap_kmh", 130.0)

            dynamic_ml_stations.append({
                "station_code": stn_code,
                "station_name": stn_name,
                "distance_km": dist_km,
                "scheduled_arrival_time": sched_arr,
                "actual_or_predicted_arrival_time": dynamic_arrival,
                "delay_minutes": dynamic_delay,
                "confidence_interval_p10_p90": [stn.get("optimistic_eta_p10"), stn.get("pessimistic_eta_p90")],
                "weather_condition": weather_desc,
                "weather_speed_cap_kmh": speed_cap,
                "eta_correction_vs_legacy_min": stn.get("eta_correction_min"),
                "prediction_engine": "GATI_SETU_DYNAMIC_PHYSICS_ML",
                "bottleneck_risk": stn.get("bottleneck_risk"),
                "platform": platform,
                "delay_status": "ON_TIME" if dynamic_delay <= 5 else "DELAYED"
            })

        return {
            "status": "success",
            "train_number": clean_no,
            "train_name": wimt_title,
            "train_type": wimt_type,
            "current_station": current_loc,
            "current_coordinates": cur_coords,
            "speed_kmph": loco_speed,
            "speed_shown": loco_speed,
            "locomotive_serial": loco_no,
            "coach_composition": coach_formation,
            "corridor_headway_km": forecast.get("downstream_corridor", {}).get("spatial_headway_km"),
            "signal_aspect": forecast.get("downstream_corridor", {}).get("signal_aspect"),
            "preceding_train": forecast.get("downstream_corridor", {}).get("preceding_train"),
            "active_formula": "GATI_SETU_DYNAMIC_WEATHER_AND_PHYSICS",
            "legacy_formula_status": "REPLACED_AND_DISABLED",
            "stations": dynamic_ml_stations,
            "gatisetu_dynamic_ml_result": dynamic_ml_stations,
            "legacy_static_algorithm_result": legacy_static_stations
        }


if __name__ == "__main__":
    adapter = WIMTEngineAdapter()
    print("Testing Where Is My Train Dynamic ML Adapter for Train 12951...")
    res = adapter.get_wimt_native_running_status("12951")
    if res.get("status") == "success":
        print(f"Train: {res['train_number']} - {res['train_name']}")
        print(f"Speed: {res['speed_kmph']} km/h, Current Loc: {res['current_station']}")
        print(f"Coaches ({len(res['coach_composition'])}): {', '.join(res['coach_composition'][:6])}...")
        print("\n=== Direct Algorithm Comparison on Where Is My Train ===")
        for leg, dyn in zip(res["legacy_static_algorithm_result"][:5], res["gatisetu_dynamic_ml_result"][:5]):
            print(f"{leg['station_code']} ({leg['station_name']}):")
            print(f"  STA Scheduled:   {leg['scheduled_arrival_time']}")
            print(f"  OLD WIMT Static: {leg['actual_or_predicted_arrival_time']} (Delay: +{leg['delay_minutes']}m)")
            print(f"  NEW GATI-SETU ML:{dyn['actual_or_predicted_arrival_time']} (Delay: +{dyn['delay_minutes']}m)")
            print(f"  Confidence Band: {dyn['confidence_interval_p10_p90']}")
            print(f"  Correction:      {dyn['eta_correction_vs_legacy_min']} min variance\n")
    else:
        print("Error:", res.get("message"))

