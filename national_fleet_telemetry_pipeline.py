"""
National Fleet Real-Time Telemetry & Dual Benchmark Pipeline
GatiSetu SIH 2026 (Problem Statement 26028)

Scans and benchmarks all 13,550 Indian Railways trains:
1. High-concurrency worker pool (50 threads) with fault tolerance.
2. Evaluates every running train against both Static WIMT/Google and GatiSetu Dynamic Physics/Weather.
3. Live incremental disk flushing (CSV + JSON) after every batch.
4. Heartbeat status file updated every 5 seconds for real-time monitoring.
5. Runs continuously in an 8-10 hour loop or as an on-demand full sweep.
"""

import sys
import os
import time
import json
import csv
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from railradar_client import RailRadarClient
from eta_engine import DynamicETAEngine


class NationalFleetPipeline:
    DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "wimt_res_only", "assets", "databases", "whereismytrain.db"
    )

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.client = RailRadarClient()
        self.engine = DynamicETAEngine()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.csv_path = os.path.join(self.base_dir, "national_telemetry_dataset.csv")
        self.heartbeat_path = os.path.join(self.base_dir, "national_scanner_heartbeat.json")
        self.report_path = os.path.join(self.base_dir, "national_scanner_report.json")
        
        self._weather_cache = {}  # stn_code -> (weather_dict, timestamp)
        self.cache_ttl = 900  # 15 minutes

        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "sweep_cycle",
                    "train_no",
                    "train_name",
                    "train_type",
                    "status",
                    "current_station_code",
                    "current_station_name",
                    "speed_kmh",
                    "current_delay_min",
                    "weather_condition",
                    "visibility_km",
                    "precipitation_mm",
                    "wind_gusts_kmh",
                    "speed_cap_kmh",
                    "is_weather_restricted",
                    "next_halt_code",
                    "next_halt_name",
                    "scheduled_arrival",
                    "static_google_eta",
                    "gatisetu_p50_eta",
                    "gatisetu_correction_min",
                    "delay_reason_tag"
                ])

    def update_heartbeat(self, sweep_cycle: int, scanned: int, total: int, active: int, weather_impacted: int, status: str = "RUNNING"):
        hb = {
            "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "sweep_cycle": sweep_cycle,
            "trains_scanned_in_cycle": scanned,
            "total_trains_in_db": total,
            "progress_percentage": round((scanned / max(1, total)) * 100.0, 1),
            "active_trains_detected": active,
            "weather_impacted_trains": weather_impacted,
            "csv_records_file": self.csv_path,
            "worker_threads": self.max_workers
        }
        with open(self.heartbeat_path, "w", encoding="utf-8") as f:
            json.dump(hb, f, indent=2)

    def load_all_trains(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.DB_PATH):
            raise FileNotFoundError(f"whereismytrain.db not found at {self.DB_PATH}")
        conn = sqlite3.connect(self.DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT train_no, train_name, train_type FROM train_info ORDER BY pop DESC")
        rows = cur.fetchall()
        conn.close()
        return [{"train_no": r[0], "train_name": r[1], "train_type": r[2]} for r in rows]

    def _get_cached_weather(self, stn_code: str) -> Dict[str, Any]:
        now = time.time()
        if stn_code in self._weather_cache:
            data, ts = self._weather_cache[stn_code]
            if now - ts < self.cache_ttl:
                return data
        w = self.engine.evaluate_weather(stn_code)
        self._weather_cache[stn_code] = (w, now)
        return w

    def evaluate_train(self, train: Dict[str, str], sweep_cycle: int) -> Dict[str, Any]:
        time.sleep(0.05)
        t_no = train["train_no"]
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
            cur_delay = data.get("delayMinutes", 0)
            cur_speed = data.get("speedKmh", 0.0)

            # Live micro-weather
            w = self._get_cached_weather(stn_code)
            vis_km = round(w.get("visibility_meters", 10000) / 1000.0, 1)
            precip = w.get("precipitation_mm", 0.0)
            wind = w.get("wind_gusts_kmh", 0.0)
            is_adverse = w.get("is_adverse", False)
            speed_cap = w.get("speed_cap_kmh", 130)

            # Next halt details & robust schedule extraction
            next_code = None
            next_name = None
            sched_time_str = "N/A"
            nxt_sch_dt = None

            for stn in data.get("route", []):
                if stn.get("isHalt") and stn.get("status") != "departed":
                    next_code = stn.get("stationCode")
                    next_name = stn.get("stationName")
                    raw_time = stn.get("scheduledArrival") or stn.get("scheduledDeparture")
                    if raw_time:
                        clean_time = raw_time.split("+")[0]
                        try:
                            nxt_sch_dt = datetime.fromisoformat(clean_time)
                            sched_time_str = nxt_sch_dt.strftime("%H:%M")
                        except Exception:
                            pass
                    break

            if not next_code:
                next_halt = data.get("nextHalt", {})
                next_code = next_halt.get("stationCode", "TERM")
                next_name = next_halt.get("stationName", "Terminus")

            static_eta = "N/A"
            gati_eta = "N/A"
            correction_min = 0.0
            reason_tag = "Normal Running"

            if nxt_sch_dt:
                static_dt = nxt_sch_dt + timedelta(minutes=cur_delay)
                static_eta = static_dt.strftime("%H:%M")
                
                # Dynamic Physics & Weather penalty
                weather_pen = 0.0
                if is_adverse and speed_cap < 110:
                    weather_pen = ((110.0 / speed_cap) - 1.0) * 18.0
                elif vis_km < 4.0:
                    weather_pen = 12.0
                elif precip > 0.2:
                    weather_pen = 8.0
                    
                bn = self.engine.JUNCTION_BOTTLENECK_SCORES.get(next_code, 2.0)
                correction_min = round(weather_pen + (bn * 0.4), 1)
                gati_dt = static_dt + timedelta(minutes=correction_min)
                gati_eta = gati_dt.strftime("%H:%M")

                if weather_pen > 0:
                    reason_tag = f"Weather Cap ({speed_cap}km/h)"
                elif bn >= 10.0:
                    reason_tag = f"Junction Bottleneck ({next_code})"
                elif cur_delay > 60:
                    reason_tag = "Cumulative Congestion"

            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sweep_cycle": sweep_cycle,
                "train_no": t_no,
                "train_name": train["train_name"],
                "train_type": train["train_type"],
                "status": "running",
                "current_station_code": stn_code,
                "current_station_name": stn_name,
                "speed_kmh": cur_speed,
                "current_delay_min": cur_delay,
                "weather_condition": w.get("condition", "Clear"),
                "visibility_km": vis_km,
                "precipitation_mm": precip,
                "wind_gusts_kmh": wind,
                "speed_cap_kmh": speed_cap,
                "is_weather_restricted": is_adverse,
                "next_halt_code": next_code,
                "next_halt_name": next_name,
                "scheduled_arrival": sched_time_str,
                "static_google_eta": static_eta,
                "gatisetu_p50_eta": gati_eta,
                "gatisetu_correction_min": correction_min,
                "delay_reason_tag": reason_tag
            }
        except Exception:
            return None

    def run_sweep(self, sweep_cycle: int = 1, batch_size: int = 100, max_trains: int = None) -> Dict[str, Any]:
        """Runs a complete or sampled sweep with immediate streaming to disk."""
        all_trains = self.load_all_trains()
        if max_trains:
            all_trains = all_trains[:max_trains]

        total = len(all_trains)
        print(f"\n[Cycle #{sweep_cycle}] Starting sweep of {total} trains using {self.max_workers} worker threads...")
        start_time = time.time()

        active_records = []
        scanned_count = 0

        # Open CSV for append
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f_csv:
            writer = csv.writer(f_csv)

            # Process in chunks of batch_size for real-time progress and disk flushing
            for i in range(0, total, batch_size):
                chunk = all_trains[i : i + batch_size]
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {executor.submit(self.evaluate_train, t, sweep_cycle): t for t in chunk}
                    for future in as_completed(futures):
                        scanned_count += 1
                        res = future.result()
                        if res:
                            active_records.append(res)
                            # Write immediately to CSV (crash-proof)
                            writer.writerow([
                                res["timestamp"],
                                res["sweep_cycle"],
                                res["train_no"],
                                res["train_name"],
                                res["train_type"],
                                res["status"],
                                res["current_station_code"],
                                res["current_station_name"],
                                res["speed_kmh"],
                                res["current_delay_min"],
                                res["weather_condition"],
                                res["visibility_km"],
                                res["precipitation_mm"],
                                res["wind_gusts_kmh"],
                                res["speed_cap_kmh"],
                                res["is_weather_restricted"],
                                res["next_halt_code"],
                                res["next_halt_name"],
                                res["scheduled_arrival"],
                                res["static_google_eta"],
                                res["gatisetu_p50_eta"],
                                res["gatisetu_correction_min"],
                                res["delay_reason_tag"]
                            ])
                f_csv.flush()

                # Update live heartbeat file after each batch
                weather_impacted = sum(1 for r in active_records if r["is_weather_restricted"])
                self.update_heartbeat(sweep_cycle, scanned_count, total, len(active_records), weather_impacted)
                
                pct = (scanned_count / total) * 100.0
                print(f"  [{scanned_count}/{total} - {pct:.1f}%] Active Trains: {len(active_records)} | Weather Restricted: {weather_impacted}")

        elapsed = time.time() - start_time
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sweep_cycle": sweep_cycle,
            "duration_seconds": round(elapsed, 1),
            "total_trains_scanned": total,
            "active_trains_found": len(active_records),
            "weather_impacted_trains": sum(1 for r in active_records if r["is_weather_restricted"]),
            "csv_records_file": self.csv_path
        }
        with open(self.report_path, "w", encoding="utf-8") as f_rep:
            json.dump(summary, f_rep, indent=2)

        print(f"[Cycle #{sweep_cycle} Complete] Scanned {total} trains in {elapsed:.1f}s. Active: {len(active_records)}. Saved to {self.csv_path}\n")
        return summary


def run_continuous_fleet_monitor(max_hours: float = 10.0, sweep_interval_min: int = 5, sample_trains: int = None):
    """Executes continuous sweep cycles over 8 to 10 hours."""
    pipeline = NationalFleetPipeline(max_workers=40)
    start_time = time.time()
    max_duration_sec = max_hours * 3600
    cycle = 1

    print("=" * 70)
    print(f"  GATI-SETU NATIONAL FLEET CONTINUOUS MONITOR (MAX: {max_hours} HOURS)")
    print(f"  Live Heartbeat : {pipeline.heartbeat_path}")
    print(f"  Live CSV Stream: {pipeline.csv_path}")
    print("=" * 70)

    while (time.time() - start_time) < max_duration_sec:
        print(f"Starting Sweep Cycle #{cycle} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            pipeline.run_sweep(sweep_cycle=cycle, batch_size=80, max_trains=sample_trains)
        except Exception as e:
            print(f"Sweep error in cycle #{cycle}: {e}")

        # Check remaining time
        elapsed_hours = (time.time() - start_time) / 3600.0
        remaining_hours = max_hours - elapsed_hours
        if remaining_hours <= 0:
            break

        print(f"Sleeping for {sweep_interval_min} minutes before next sweep cycle (Remaining: {remaining_hours:.1f} hrs)...")
        time.sleep(sweep_interval_min * 60)
        cycle += 1

    pipeline.update_heartbeat(cycle, 0, 0, 0, 0, status="COMPLETED")
    print(f"Monitoring completed after {elapsed_hours:.2f} hours.")


if __name__ == "__main__":
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run_continuous_fleet_monitor(max_hours=hours, sweep_interval_min=5, sample_trains=limit)

