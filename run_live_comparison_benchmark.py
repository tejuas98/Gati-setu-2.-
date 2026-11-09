"""
Live Formula Benchmark: Static WIMT/Google vs GatiSetu Physics & Weather Engine
Directly evaluates the exact mathematical divergence between:
1. Static Delay Extrapolation (Where Is My Train / Google)
2. GatiSetu Dynamic Physics & Open-Meteo Weather Model
"""

import sys
import os
import time
import csv
from datetime import datetime, timedelta

from railradar_client import RailRadarClient
from eta_engine import DynamicETAEngine


def run_benchmark():
    client = RailRadarClient()
    engine = DynamicETAEngine()
    
    # Priority active trains across Northern, Western, Central, Southern, and Eastern corridors
    active_test_trains = [
        '12779', # Goa Express (Central to North)
        '22661', # Sethu SF Express (Southern Coastal Rain Corridor)
        '12951', # Tejas Rajdhani (Western High-Speed Trunk)
        '12138', # Punjab Mail (Northern to Central)
        '12361', # Mumbai CSMT SF Express (Eastern to Central)
        '12623', # Thiruvananthapuram Mail (Southern)
        '12626', # Kerala Express (Grand Trunk North-South)
        '12424', # Dibrugarh Rajdhani (Northeast Corridor)
        '12302', # Howrah Rajdhani (Eastern High-Density Corridor)
        '12861', # Mahbubnagar SF Express (South Central)
        '14114', # Subedarganj Express (Northern Night Haze)
        '15014'  # Ranikhet Express (Northern Foothills)
    ]
    
    out_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_formula_comparison_benchmark.csv")
    results = []
    
    print("=" * 80)
    print("  LIVE BENCHMARK: STATIC FORMULA (GOOGLE) VS GATISETU DYNAMIC PHYSICS")
    print("=" * 80)
    
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "train_no",
            "train_name",
            "current_station",
            "current_delay_min",
            "next_halt_name",
            "next_halt_code",
            "scheduled_arrival",
            "static_google_eta",
            "gatisetu_physics_eta",
            "delta_difference_min",
            "weather_condition",
            "visibility_km",
            "precipitation_mm",
            "operational_cause_tag"
        ])
        
        for t_no in active_test_trains:
            time.sleep(0.4)
            try:
                res = client.get_live_status(t_no)
                if not res or not res.get("success"):
                    continue
                data = res.get("data", {})
                if data.get("status") != "running":
                    continue
                    
                t_name = data.get("trainName", "Express")
                cur_delay = data.get("delayMinutes", 0)
                cur_loc = data.get("currentLocation", {})
                cur_stn = cur_loc.get("stationName", "En Route")
                
                # Resolve next halt
                nxt_code = None
                nxt_name = None
                nxt_sch_dt = None
                
                for s in data.get("route", []):
                    if s.get("isHalt") and s.get("status") != "departed":
                        nxt_code = s.get("stationCode")
                        nxt_name = s.get("stationName")
                        sch_str = s.get("scheduledArrival") or s.get("scheduledDeparture")
                        if sch_str:
                            clean_time = sch_str.split("+")[0]
                            nxt_sch_dt = datetime.fromisoformat(clean_time)
                        break
                        
                if not nxt_code or not nxt_sch_dt:
                    continue
                    
                # 1. Static Formula (Where Is My Train / Google):
                # ETA_static = Scheduled + Current Delay
                static_eta_dt = nxt_sch_dt + timedelta(minutes=cur_delay)
                
                # 2. Weather at Next Station (Open-Meteo)
                w = engine.evaluate_weather(nxt_code)
                vis = round(w.get("visibility_meters", 10000) / 1000.0, 1)
                precip = w.get("precipitation_mm", 0.0)
                wind = w.get("wind_gusts_kmh", 0.0)
                cond = w.get("condition", "Clear")
                
                # 3. GatiSetu Dynamic Physics & Weather Model:
                # Delta_weather + Delta_junction + Delta_physics
                weather_pen = 0.0
                if w.get("is_adverse") and w.get("speed_cap_kmh"):
                    weather_pen = ((110.0 / w["speed_cap_kmh"]) - 1.0) * 18.0
                elif vis < 4.0:
                    weather_pen = 12.0 # fog speed restriction
                elif precip > 0.2:
                    weather_pen = 8.0  # wet rail adhesion cap
                    
                bn = engine.JUNCTION_BOTTLENECK_SCORES.get(nxt_code, 2.0)
                delta_min = round(weather_pen + (bn * 0.4), 1)
                gatisetu_eta_dt = static_eta_dt + timedelta(minutes=delta_min)
                
                tag = "Normal Running"
                if weather_pen > 0:
                    tag = f"Weather Cap ({w.get('speed_cap_kmh', 60)}km/h)"
                elif bn >= 10.0:
                    tag = f"Junction Bottleneck ({nxt_code})"
                elif cur_delay > 60:
                    tag = "Cumulative Congestion"
                    
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    t_no,
                    t_name,
                    cur_stn,
                    cur_delay,
                    nxt_name,
                    nxt_code,
                    nxt_sch_dt.strftime("%H:%M"),
                    static_eta_dt.strftime("%H:%M"),
                    gatisetu_eta_dt.strftime("%H:%M"),
                    delta_min,
                    cond,
                    vis,
                    precip,
                    tag
                ])
                f.flush()
                
                results.append({
                    "no": t_no,
                    "name": t_name,
                    "cur_stn": cur_stn,
                    "delay": cur_delay,
                    "nxt_code": nxt_code,
                    "nxt_name": nxt_name,
                    "sch": nxt_sch_dt.strftime("%H:%M"),
                    "static": static_eta_dt.strftime("%H:%M"),
                    "gati": gatisetu_eta_dt.strftime("%H:%M"),
                    "diff": delta_min,
                    "weather": f"{cond} (Vis {vis}km)",
                    "tag": tag
                })
                
            except Exception as e:
                print(f"Error checking #{t_no}: {e}")
                
    print(f"{'Train':8s} {'Name':22s} {'Next Halt':16s} {'Sch':5s} {'Static ETA':10s} {'GatiSetu ETA':12s} {'Diff':6s} {'Cause Tag':22s}")
    print("-" * 105)
    for r in results:
        print(f"#{r['no']:7s} {r['name'][:20]:22s} {r['nxt_code']:5s} ({r['nxt_name'][:8]:8s}) {r['sch']:5s} {r['static']:10s} {r['gati']:12s} {r['diff']:+4.1f}m  {r['tag']:22s}")
    print("=" * 105)
    print(f"Results saved to: {out_csv}")


if __name__ == "__main__":
    run_benchmark()

