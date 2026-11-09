"""
Continuous Train Telemetry & Live Prediction Benchmark Logger
GatiSetu SIH 2026 (Problem Statement 26028)

Monitors a live train continuously over 5 to 10 hours:
1. Polls real-time locomotive GPS, speed, and station events.
2. Queries live Open-Meteo weather for active coordinates.
3. Records Static WIMT / Google Prediction vs GatiSetu Dynamic Prediction.
4. Captures ground-truth actual arrival timestamps as they occur.
5. Appends live logs to a CSV file for empirical benchmark verification.
"""

import sys
import os
import time
import csv
from datetime import datetime
from railradar_client import RailRadarClient
from eta_engine import DynamicETAEngine


def run_continuous_logger(train_number: str, interval_seconds: int = 120, max_hours: float = 10.0):
    client = RailRadarClient()
    engine = DynamicETAEngine()
    
    clean_no = str(train_number).strip().lstrip("0")
    csv_filename = f"benchmark_telemetry_log_{clean_no}.csv"
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
    
    file_exists = os.path.exists(csv_path)
    
    print(f"Starting Continuous Benchmark Logger for Train #{clean_no}")
    print(f"Log Destination: {csv_path}")
    print(f"Poll Interval: {interval_seconds}s | Max Duration: {max_hours} hours")
    
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "poll_timestamp",
                "train_number",
                "current_station_code",
                "current_station_name",
                "status",
                "delay_minutes",
                "loco_speed_kmh",
                "weather_condition",
                "visibility_km",
                "precipitation_mm",
                "wind_gusts_kmh",
                "next_halt_code",
                "next_halt_name",
                "next_halt_scheduled",
                "static_google_eta",
                "gatisetu_p50_eta",
                "actual_arrival_event"
            ])
            f.flush()
            
        start_time = time.time()
        max_duration_sec = max_hours * 3600
        
        while (time.time() - start_time) < max_duration_sec:
            poll_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                res = client.get_live_status(clean_no)
                if not res or not res.get("success"):
                    print(f"[{poll_now}] Train #{clean_no}: Waiting for live data stream...")
                    time.sleep(interval_seconds)
                    continue
                
                d = res["data"]
                cur_loc = d.get("currentLocation", {})
                cur_stn_code = cur_loc.get("stationCode", "EN_ROUTE")
                cur_stn_name = cur_loc.get("stationName", "En Route")
                status = cur_loc.get("status", d.get("status", "running"))
                cur_delay = d.get("delayMinutes", 0)
                cur_speed = d.get("speedKmh", 0.0)
                
                next_halt = d.get("nextHalt", {})
                next_code = next_halt.get("stationCode", "NONE")
                next_name = next_halt.get("stationName", "None")
                
                # Fetch route station info
                next_sch = "N/A"
                for stn in d.get("route", []):
                    if stn.get("stationCode") == next_code:
                        next_sch = stn.get("scheduledArrival") or stn.get("scheduledDeparture") or "N/A"
                        break
                
                # Dynamic Weather at current coordinates
                w = engine.evaluate_weather(cur_stn_code)
                vis_km = round(w.get("visibility_meters", 10000) / 1000.0, 1)
                precip = w.get("precipitation_mm", 0.0)
                wind = w.get("wind_gusts_kmh", 0.0)
                
                # Dynamic Forecast
                forecast = engine.forecast_train_eta(clean_no)
                gati_eta = "N/A"
                static_eta = "N/A"
                
                if forecast.get("success"):
                    for up in forecast.get("upcoming_stations", []):
                        if up.get("station_code") == next_code:
                            gati_eta = up.get("dynamic_forecast_p50", "N/A")
                            static_eta = up.get("naive_ntes_eta", "N/A")
                            break
                
                actual_event = f"At {cur_stn_name} (+{cur_delay}m)" if status in ["at-station", "departed"] else "Cruising"
                
                writer.writerow([
                    poll_now,
                    clean_no,
                    cur_stn_code,
                    cur_stn_name,
                    status,
                    cur_delay,
                    cur_speed,
                    w.get("condition", "Clear"),
                    vis_km,
                    precip,
                    wind,
                    next_code,
                    next_name,
                    next_sch,
                    static_eta,
                    gati_eta,
                    actual_event
                ])
                f.flush()
                
                print(f"[{poll_now}] #{clean_no} @ {cur_stn_name} | Delay: {cur_delay}m | Next: {next_name} | Static: {static_eta} | GatiSetu: {gati_eta} | Weather: {w.get('condition')}")
                
            except Exception as e:
                print(f"[{poll_now}] Polling error: {e}")
                
            time.sleep(interval_seconds)
            
    print(f"Continuous monitoring completed ({max_hours} hours). Log saved to {csv_path}")


if __name__ == "__main__":
    t_no = sys.argv[1] if len(sys.argv) > 1 else "22661"
    run_continuous_logger(t_no, interval_seconds=120, max_hours=10.0)

