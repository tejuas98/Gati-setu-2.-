"""
GATI-SETU: Dynamic Train ETA Forecast & Section Control API Server
Problem Statement 26028 (Smart India Hackathon 2026 - Ministry of Railways)

FastAPI Server providing high-throughput endpoints for:
1. Passenger Mobile Apps (Dynamic ETA with P10/P50/P90 confidence intervals)
2. Station Displays (PIDS - Dynamic arrival boards with platform conflict detection)
3. Section Controller Dashboards (Downstream headway, signal aspects, bottleneck scoring)
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

# Ensure current directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eta_engine import DynamicETAEngine
from railradar_client import RailRadarClient
from railjournal_client import RailJournalClient
from whereismytrain_extractor import WhereIsMyTrainExtractor
from wimt_engine_adapter import WIMTEngineAdapter

app = FastAPI(
    title="GATI-SETU: Dynamic Railway ETA Engine",
    description="Multi-factor Spatio-Temporal Train Arrival Forecasting System for Indian Railways",
    version="1.0.0"
)

# Enable CORS for mobile apps and web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
engine = DynamicETAEngine()
rr_client = RailRadarClient()
rj_client = RailJournalClient()
wimt_adapter = WIMTEngineAdapter()


@app.get("/")
def root():
    return {
        "system": "GATI-SETU Dynamic ETA Engine",
        "problem_statement_id": "26028",
        "ministry": "Ministry of Railways",
        "status": "OPERATIONAL",
        "active_telemetry_sources": ["RailRadar /app/v1/", "RailJournal CDN & Loco Telemetry", "WIMT Offline Assets"],
        "docs_url": "/docs"
    }


@app.get("/api/v1/forecast/{train_number}")
def get_train_forecast(train_number: str):
    """
    Dynamic ETA Forecast for Passenger Mobile Apps and Controllers.
    Returns P10 (Optimistic), P50 (Expected), P90 (Pessimistic) arrival times,
    downstream signal headway, and locomotive power telemetry.
    """
    result = engine.forecast_train_eta(train_number)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Train forecast unavailable"))
    return result


@app.get("/api/v1/station/{station_code}/platform-dispatch")
def get_station_dispatch(station_code: str, hours: int = Query(4, ge=1, le=12)):
    """
    Station Display & Section Controller API.
    Evaluates upcoming train arrivals, applies dynamic delay forecasts,
    and detects platform allocation conflicts.
    """
    stn = station_code.upper().strip()
    board = rr_client.get_station_live_board(stn, hours=hours)
    if not board.get("success"):
        raise HTTPException(status_code=404, detail=f"No active station board for {stn}")

    trains = board.get("data", {}).get("trains", [])
    dispatch_list = []
    platform_timeline = {}

    for t in trains[:15]:
        t_no = str(t.get("trainNumber", ""))
        t_name = t.get("trainName", "")
        sched_time = t.get("scheduledTime", "")
        delay = float(t.get("delayMinutes", 0))
        platform = str(t.get("platform", "1"))

        # Calculate Dynamic Forecast delta using engine residual heuristics
        bottleneck = DynamicETAEngine.JUNCTION_BOTTLENECK_SCORES.get(stn, 0.0)
        dynamic_delay = delay + (bottleneck * 0.4)
        
        # Conflict detection: Check if another train is scheduled on the same platform within 15 min
        conflict = False
        conflicting_train = None
        if platform in platform_timeline:
            prev_train, prev_delay = platform_timeline[platform]
            if abs(dynamic_delay - prev_delay) < 15.0:
                conflict = True
                conflicting_train = prev_train
        platform_timeline[platform] = (t_no, dynamic_delay)

        dispatch_list.append({
            "train_number": t_no,
            "train_name": t_name,
            "scheduled_time": sched_time,
            "static_delay_min": delay,
            "dynamic_forecast_delay_min": round(dynamic_delay, 1),
            "assigned_platform": platform,
            "platform_conflict_detected": conflict,
            "conflicting_train": conflicting_train,
            "action_recommendation": f"RE-ALLOCATE PLATFORM (Conflict with #{conflicting_train})" if conflict else "PROCEED NORMAL"
        })

    return {
        "station_code": stn,
        "station_name": board.get("data", {}).get("station", {}).get("name", stn),
        "evaluation_window_hours": hours,
        "total_inbound_trains": len(dispatch_list),
        "inbound_dispatch": dispatch_list
    }


@app.get("/api/v1/corridor/congestion")
def get_corridor_congestion():
    """
    Network-wide Downstream Track Congestion & Bottleneck Analysis.
    Scans nationwide telemetry to pinpoint congested sections.
    """
    radar = rr_client.get_live_radar_map()
    markers = rj_client.get_live_markers()

    total_active = len(radar)
    delayed_over_30 = sum(1 for t in radar if t.get("delay_minutes", 0) > 30)
    delayed_over_60 = sum(1 for t in radar if t.get("delay_minutes", 0) > 60)

    # Calculate average network speed
    moving_trains = [t.get("speed_kmh", 0) for t in radar if t.get("speed_kmh", 0) > 5]
    avg_speed = round(sum(moving_trains) / len(moving_trains), 1) if moving_trains else 0.0

    return {
        "timestamp": datetime.now().isoformat(),
        "total_active_running_trains": total_active,
        "locomotives_in_marker_feed": markers.get("count", 0),
        "network_average_running_speed_kmh": avg_speed,
        "trains_delayed_over_30m": delayed_over_30,
        "trains_delayed_over_60m": delayed_over_60,
        "corridor_punctuality_index": round((1.0 - (delayed_over_30 / max(1, total_active))) * 100.0, 1),
        "critical_junction_status": {
            k: {
                "bottleneck_weight": v,
                "status": "CONGESTED" if v >= 12.0 else "NORMAL"
            } for k, v in DynamicETAEngine.JUNCTION_BOTTLENECK_SCORES.items()
        }
    }


@app.get("/api/v1/radar/live-trains")
def get_live_radar_trains(limit: int = Query(300, ge=1, le=3000)):
    """
    Supplies active running trains with coordinates, speed, and delay for the Section Controller Map.
    """
    trains = rr_client.get_live_radar_map()
    return {
        "total_active_nationwide": len(trains),
        "returned_count": min(len(trains), limit),
        "trains": trains[:limit]
    }


@app.get("/api/v1/radar/route-track/{train_number}")
def get_train_route_track(train_number: str):
    """
    Returns high-precision GIS LineString track geometry (2,000+ coordinates)
    for rendering exact railway lines on the Section Controller Radar.
    """
    clean_no = str(train_number).strip().lstrip("0")
    route = rr_client.get_route_geometry(clean_no)
    if not route.get("success"):
        raise HTTPException(status_code=404, detail=f"Track geometry not found for train {clean_no}")
    
    geom = route.get("data", {}).get("geojson", {}).get("geometry", {})
    return {
        "train_number": clean_no,
        "geometry_type": geom.get("type", "LineString"),
        "coordinates": geom.get("coordinates", [])
    }


@app.get("/api/v1/weather/zones")
def get_active_weather_zones():
    """
    Returns active adverse weather zones across Indian Railways divisions
    (Dense Winter Fog, Monsoon Flooding, Extreme Summer Heat).
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "zones": DynamicETAEngine.WEATHER_ZONES
    }


@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the Section Controller and Passenger Web Dashboard."""
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard file not found.</h1>"


@app.get("/wimt", response_class=HTMLResponse)
def serve_wimt_mobile_app():
    """Serves the Where Is My Train Interactive Mobile App running GATI-SETU ML."""
    wimt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wimt_interactive_app.html")
    if os.path.exists(wimt_path):
        with open(wimt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>WIMT Mobile App file not found.</h1>"


@app.get("/wimt_relay/running_status")
def get_wimt_relay_status(trainNo: str = Query("12951")):
    """
    Direct endpoint intercepted from patched Where Is My Train APK.
    Replaces WIMT's legacy static formula with the GATI-SETU Spatio-Temporal ML Engine.
    """
    res = wimt_adapter.get_wimt_native_running_status(trainNo)
    if res.get("status") != "success":
        raise HTTPException(status_code=404, detail=res.get("message", "Train not found"))
    return res


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)

