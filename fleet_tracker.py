"""
GatiSetu National Fleet Engine: All-India Concurrent Train Monitoring
Smart India Hackathon 2026 (Problem Statement 26028)

Monitors, tracks, and evaluates dynamic physics & weather across
the entire Indian Railways passenger network simultaneously.

Architecture:
1. Loads all 13,550 trains from local whereismytrain.db.
2. Concurrent Worker Pool evaluates real-time telemetry across active runs.
3. Spatial Weather Caching (15-min TTL) prevents API bottlenecks.
4. Calculates national network statistics (Delay causes, On-time %, Weather speed caps).
5. Exports live national fleet snapshot to national_fleet_telemetry.json.
"""

import sys
import os
import time
import json
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from railradar_client import RailRadarClient
from eta_engine import DynamicETAEngine


class NationalFleetEngine:
    DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "wimt_res_only", "assets", "databases", "whereismytrain.db"
    )

    def __init__(self, max_workers: int = 25):
        self.max_workers = max_workers
        self.client = RailRadarClient()
        self.eta_engine = DynamicETAEngine()
        self._weather_cache = {}  # (lat_round, lon_round) -> (weather_data, timestamp)
        self.cache_ttl_sec = 900  # 15 minutes

    def get_all_train_numbers(self, limit: int = None) -> List[Dict[str, str]]:
        """Loads train master records from offline whereismytrain.db."""
        if not os.path.exists(self.DB_PATH):
            raise FileNotFoundError(f"whereismytrain.db not found at {self.DB_PATH}")

        conn = sqlite3.connect(self.DB_PATH)
        cur = conn.cursor()
        query = "SELECT train_no, train_name, train_type FROM train_info ORDER BY pop DESC"
        if limit:
            query += f" LIMIT {limit}"
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        return [{"train_no": r[0], "train_name": r[1], "train_type": r[2]} for r in rows]

    def _get_cached_weather(self, stn_code: str) -> Dict[str, Any]:
        """Spatial weather cache with 15-minute TTL to handle fleet-wide scale."""
        now = time.time()
        if stn_code in self._weather_cache:
            data, ts = self._weather_cache[stn_code]
            if now - ts < self.cache_ttl_sec:
                return data

        w = self.eta_engine.evaluate_weather(stn_code)
        self._weather_cache[stn_code] = (w, now)
        return w

    def evaluate_single_train(self, train_meta: Dict[str, str]) -> Dict[str, Any]:
        """Evaluates live status, weather, and physics for a single train."""
        t_no = train_meta["train_no"]
        try:
            res = self.client.get_live_status(t_no)
            if not res or not res.get("success"):
                return None

            data = res.get("data", {})
            if data.get("status") != "running":
                return None

            cur_loc = data.get("currentLocation", {})
            stn_code = cur_loc.get("stationCode", "EN_ROUTE")
            stn_name = cur_loc.get("stationName", "En Route")
            delay = data.get("delayMinutes", 0)
            speed = data.get("speedKmh", 0.0)

            # Micro-weather at current station
            weather = self._get_cached_weather(stn_code)

            return {
                "train_no": t_no,
                "train_name": train_meta["train_name"],
                "train_type": train_meta["train_type"],
                "current_station_code": stn_code,
                "current_station_name": stn_name,
                "delay_minutes": delay,
                "speed_kmh": speed,
                "weather_condition": weather.get("condition", "Clear"),
                "visibility_km": round(weather.get("visibility_meters", 10000) / 1000.0, 1),
                "is_weather_impacted": weather.get("is_adverse", False),
                "speed_cap_kmh": weather.get("speed_cap_kmh", 130),
                "delay_category": (
                    "ON_TIME" if delay <= 15 else (
                        "MODERATE_DELAY" if delay <= 60 else "SEVERE_DELAY"
                    )
                )
            }
        except Exception:
            return None

    def scan_fleet(self, sample_size: int = 150) -> Dict[str, Any]:
        """Scans multiple trains concurrently across the national grid."""
        trains = self.get_all_train_numbers(limit=sample_size)
        start_time = time.time()
        print(f"Scanning {len(trains)} trains concurrently with {self.max_workers} worker threads...")

        active_fleet = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_train = {executor.submit(self.evaluate_single_train, t): t for t in trains}
            for future in as_completed(future_to_train):
                result = future.result()
                if result:
                    active_fleet.append(result)

        elapsed = time.time() - start_time

        # Compute National Fleet KPIs
        total_active = len(active_fleet)
        if total_active > 0:
            avg_delay = sum(t["delay_minutes"] for t in active_fleet) / total_active
            on_time_count = sum(1 for t in active_fleet if t["delay_category"] == "ON_TIME")
            on_time_pct = (on_time_count / total_active) * 100.0
            weather_affected = sum(1 for t in active_fleet if t["is_weather_impacted"])
        else:
            avg_delay = 0.0
            on_time_pct = 0.0
            weather_affected = 0

        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_duration_seconds": round(elapsed, 2),
            "trains_checked": len(trains),
            "active_running_trains": total_active,
            "on_time_percentage": round(on_time_pct, 1),
            "average_network_delay_minutes": round(avg_delay, 1),
            "weather_impacted_trains": weather_affected,
            "active_fleet_sample": active_fleet
        }

        # Export live snapshot
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "national_fleet_telemetry.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    engine = NationalFleetEngine(max_workers=25)
    report = engine.scan_fleet(sample_size=count)

    print("\n" + "=" * 65)
    print(f"  GATI-SETU NATIONAL FLEET SUMMARY ({report['timestamp']})")
    print("=" * 65)
    print(f"Total Trains Evaluated : {report['trains_checked']} trains in {report['scan_duration_seconds']}s")
    print(f"Active Running Trains  : {report['active_running_trains']}")
    print(f"Network On-Time Rate   : {report['on_time_percentage']}%")
    print(f"Average Network Delay  : {report['average_network_delay_minutes']} minutes")
    print(f"Weather-Restricted Runs: {report['weather_impacted_trains']} trains")
    print("-" * 65)
    print(f"{'Train':8s} {'Name':25s} {'Station':18s} {'Delay':8s} {'Weather':15s}")
    print("-" * 65)
    for t in report["active_fleet_sample"][:12]:
        print(f"#{t['train_no']:7s} {t['train_name'][:24]:25s} {t['current_station_name'][:17]:18s} +{t['delay_minutes']}m     {t['weather_condition'][:14]:15s}")
    print("=" * 65)
    print(f"Full live JSON snapshot exported to national_fleet_telemetry.json")

