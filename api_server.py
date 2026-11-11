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
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

# Ensure current directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eta_engine import DynamicETAEngine
from railradar_client import RailRadarClient
from railjournal_client import RailJournalClient
from whereismytrain_extractor import WhereIsMyTrainExtractor
from wimt_engine_adapter import WIMTEngineAdapter
from edge_location_engine import (
    edge_engine,
    EdgeLocationReport,
    MotionSensorData,
    CALIBRATED_CELL_TOWERS
)

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

_forecast_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_congestion_cache: Dict[str, Any] = {}

def get_cached_forecast(train_no: str, ttl: float = 45.0) -> Dict[str, Any]:
    now = time.time()
    clean = str(train_no).strip().lstrip("0")
    if clean in _forecast_cache:
        t_cached, data = _forecast_cache[clean]
        if (now - t_cached) < ttl:
            return data
    data = engine.forecast_train_eta(clean)
    if data.get("success"):
        _forecast_cache[clean] = (now, data)
    return data


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
    result = get_cached_forecast(train_number)
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
        "station": stn,
        "station_code": stn,
        "station_name": board.get("data", {}).get("station", {}).get("name", stn),
        "evaluation_window_hours": hours,
        "total_inbound_trains": len(dispatch_list),
        "inbound_dispatch": dispatch_list
    }


@app.get("/api/v1/corridor/signal-aspects/{train_number}")
def get_corridor_signal_aspects(train_number: str):
    """
    Automatic Block Signaling (ABS) & Corridor Headway Ingestion Endpoint.
    Returns the real-time downstream 4-aspect signal chain, preceding train identifier,
    spatial headway distance, and Section Controller precedence action for train_number.
    """
    clean_no = str(train_number).strip().lstrip("0")
    forecast = get_cached_forecast(clean_no)
    if not forecast.get("success"):
        raise HTTPException(status_code=404, detail=forecast.get("error", "Train corridor data unavailable"))

    corridor = forecast.get("downstream_corridor", {})
    headway_km = corridor.get("spatial_headway_km", 25.0)
    preceding = corridor.get("preceding_train", "Corridor Clear Ahead")
    aspect = corridor.get("signal_aspect", "CLEAR_GREEN")
    recom = corridor.get("controller_recommendation")

    # Generate upcoming signal chain along downstream automatic block sections
    signal_chain = []
    block_length_km = 3.0
    accumulated_km = 0.0

    for i in range(1, 6):
        sig_km = round(accumulated_km + (i * block_length_km), 1)
        if headway_km < (i * block_length_km):
            sig_aspect = "DANGER_RED" if (headway_km < (i - 1) * block_length_km) else "CAUTION_SINGLE_YELLOW"
            speed_cap = 0.0 if sig_aspect == "DANGER_RED" else 45.0
            block_status = "OCCUPIED"
        elif headway_km < ((i + 1) * block_length_km):
            sig_aspect = "ATTENTION_DOUBLE_YELLOW"
            speed_cap = 80.0
            block_status = "APPROACHING_OCCUPIED"
        else:
            sig_aspect = "CLEAR_GREEN"
            speed_cap = 130.0
            block_status = "CLEAR"

        signal_chain.append({
            "signal_id": f"ABS-SIG-{i:02d}",
            "distance_ahead_km": sig_km,
            "signal_aspect": sig_aspect,
            "permissible_speed_kmh": speed_cap,
            "block_occupancy": block_status
        })

    return {
        "status": "success",
        "train_number": clean_no,
        "train_name": forecast.get("train_name"),
        "current_station": forecast.get("current_location"),
        "spatial_headway_km": headway_km,
        "preceding_train": preceding,
        "current_signal_aspect": aspect,
        "controller_recommendation": recom,
        "downstream_signal_chain": signal_chain
    }


@app.get("/api/v1/corridor/congestion")
def get_corridor_congestion():
    """
    Network-wide Downstream Track Congestion & Bottleneck Analysis.
    Scans nationwide telemetry to pinpoint congested sections.
    """
    now = time.time()
    if _congestion_cache.get("data") and (now - _congestion_cache.get("timestamp_epoch", 0)) < 45.0:
        return _congestion_cache["data"]

    radar = rr_client.get_live_radar_map()
    markers = rj_client.get_live_markers()

    total_active = len(radar)
    delayed_over_30 = sum(1 for t in radar if t.get("delay_minutes", 0) > 30)
    delayed_over_60 = sum(1 for t in radar if t.get("delay_minutes", 0) > 60)

    # Calculate average network speed
    moving_trains = [t.get("speed_kmh", 0) for t in radar if t.get("speed_kmh", 0) > 5]
    avg_speed = round(sum(moving_trains) / len(moving_trains), 1) if moving_trains else 0.0

    res = {
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
    _congestion_cache["timestamp_epoch"] = now
    _congestion_cache["data"] = res
    return res


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


@app.get("/api/v1/weather/live/{station_code}")
def get_station_live_weather(station_code: str):
    """
    Returns live Open-Meteo weather observations (visibility, temperature, precipitation)
    and Indian Railways G&SR safety speed cap for any station.
    """
    stn = station_code.upper().strip()
    from wimt_core.weather_engine import WeatherSafetyEngine
    w = WeatherSafetyEngine.evaluate_station_weather(stn)
    coords = WeatherSafetyEngine.get_coordinates_for_station(stn)
    return {
        "station_code": stn,
        "coordinates": {"lat": coords[0], "lng": coords[1]} if coords else None,
        "condition": w.condition_name,
        "speed_cap_kmh": w.speed_cap_kmh,
        "safety_protocol": w.safety_protocol,
        "penalty_multiplier": w.penalty_multiplier,
        "is_adverse": w.is_adverse,
        "risk_level": w.risk_level,
        "source": w.source,
        "visibility_meters": w.visibility_meters,
        "temperature_celsius": w.temperature_celsius,
        "precipitation_mm": w.precipitation_mm,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/search/trains-between")
def search_trains_between_stations(
    from_station: str = Query(..., description="Origin station code, e.g. BSL or MMCT"),
    to_station: str = Query(..., description="Destination station code, e.g. NK or NDLS"),
    date: Optional[str] = Query(None, description="Travel date in YYYY-MM-DD")
):
    """
    Finds all Indian Railways trains running between two stations.
    """
    stn_from = from_station.upper().strip()
    stn_to = to_station.upper().strip()
    travel_date = date or datetime.now().strftime("%Y-%m-%d")

    res = rr_client.get_trains_between(stn_from, stn_to, travel_date)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=f"No trains found between {stn_from} and {stn_to}")

    trains = res.get("data", {}).get("trains", [])
    output_list = []
    for t in trains:
        tr = t.get("train", {})
        fr = t.get("from", {})
        to = t.get("to", {})
        output_list.append({
            "train_number": tr.get("number"),
            "train_name": tr.get("name"),
            "train_type": tr.get("type"),
            "running_days": tr.get("runDays", []),
            "from_station": fr.get("code"),
            "from_station_name": fr.get("name"),
            "departure_time": fr.get("departure"),
            "to_station": to.get("code"),
            "to_station_name": to.get("name"),
            "arrival_time": to.get("arrival"),
            "distance_km": t.get("distance"),
            "duration_minutes": t.get("duration"),
            "total_halts": t.get("totalHaltsBetween")
        })

    return {
        "success": True,
        "from_station": stn_from,
        "to_station": stn_to,
        "date": travel_date,
        "total_trains": len(output_list),
        "trains": output_list
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


class MotionSensorIn(BaseModel):
    linear_z_variance: float = Field(0.0, description="m/s^2 vertical harmonic rail vibration variance")
    angular_speed_rad_s: float = Field(0.0, description="rad/s turn rate from gyroscope")
    step_frequency_hz: float = Field(0.0, description="Hz pedestrian cadence")


class EdgeReportIn(BaseModel):
    device_id: str = Field(..., description="Unique client installation ID")
    train_number: str = Field(..., description="Indian Railways train number (e.g. 12951 or 22946)")
    timestamp_utc: Optional[str] = Field(None, description="ISO 8601 UTC timestamp")
    source_type: str = Field("SATELLITE_GPS", description="SATELLITE_GPS, CELL_TRIANGULATION, or HYBRID_FUSED")
    latitude: float = Field(0.0, description="WGS84 Latitude")
    longitude: float = Field(0.0, description="WGS84 Longitude")
    accuracy_m: float = Field(15.0, description="Estimated accuracy radius in meters")
    speed_kmh: float = Field(0.0, description="Current speed in km/h")
    bearing_deg: float = Field(0.0, description="Course heading in degrees")
    cell_id: Optional[str] = Field(None, description="Compound cellular key {MCC}_{MNC}_{LAC}_{CID}")
    signal_strength_dbm: int = Field(-85, description="Cellular signal strength in dBm")
    sensors: Optional[MotionSensorIn] = None


class EdgeBatchIn(BaseModel):
    train_number: str = Field(..., description="Train number for buffered reports")
    reports: List[EdgeReportIn] = Field(..., description="List of chronologically ordered edge reports")


@app.post("/api/v1/telemetry/edge_ingest")
def ingest_edge_telemetry(payload: EdgeReportIn):
    """
    Edge Location Data Collection Endpoint (Problem Statement 26028).
    Ingests live GPS, Cell Tower ({MCC}_{MNC}_{LAC}_{CID}), and sensor fusion
    data from passenger mobile clients, snaps coordinates to the rail centerline,
    and updates the dynamic train running state.
    """
    ts = payload.timestamp_utc or datetime.utcnow().isoformat()
    sens = MotionSensorData()
    if payload.sensors:
        sens = MotionSensorData(
            linear_z_variance=payload.sensors.linear_z_variance,
            angular_speed_rad_s=payload.sensors.angular_speed_rad_s,
            step_frequency_hz=payload.sensors.step_frequency_hz
        )

    report = EdgeLocationReport(
        device_id=payload.device_id,
        train_number=payload.train_number,
        timestamp_utc=ts,
        source_type=payload.source_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
        speed_kmh=payload.speed_kmh,
        bearing_deg=payload.bearing_deg,
        cell_id=payload.cell_id,
        signal_strength_dbm=payload.signal_strength_dbm,
        sensors=sens
    )

    consensus = edge_engine.ingest_edge_report(report)
    return {
        "status": "success",
        "train_number": consensus.train_number,
        "last_updated_utc": consensus.last_updated_utc,
        "consensus_coordinates": {
            "latitude": consensus.consensus_lat,
            "longitude": consensus.consensus_lng
        },
        "consensus_speed_kmh": consensus.consensus_speed_kmh,
        "track_chainage_km": consensus.track_chainage_km,
        "nearest_station": consensus.nearest_station,
        "distance_to_station_km": consensus.distance_to_station_km,
        "cross_track_error_m": consensus.cross_track_error_m,
        "in_train_confidence_pct": consensus.in_train_confidence_pct,
        "motion_classification": consensus.motion_classification,
        "active_edge_devices": consensus.active_edge_devices_count,
        "matched_corridor": consensus.matched_corridor,
        "is_halted": consensus.is_halted
    }


@app.post("/api/v1/telemetry/edge_batch_ingest")
def ingest_edge_batch_telemetry(batch: EdgeBatchIn):
    """
    Offline Edge Buffer Synchronization Endpoint.
    Ingests buffered location reports collected while passing through cellular
    dead zones once network connectivity is re-established.
    """
    processed = 0
    latest_status = None
    for r in batch.reports:
        ts = r.timestamp_utc or datetime.utcnow().isoformat()
        sens = MotionSensorData()
        if r.sensors:
            sens = MotionSensorData(
                linear_z_variance=r.sensors.linear_z_variance,
                angular_speed_rad_s=r.sensors.angular_speed_rad_s,
                step_frequency_hz=r.sensors.step_frequency_hz
            )
        report = EdgeLocationReport(
            device_id=r.device_id,
            train_number=r.train_number,
            timestamp_utc=ts,
            source_type=r.source_type,
            latitude=r.latitude,
            longitude=r.longitude,
            accuracy_m=r.accuracy_m,
            speed_kmh=r.speed_kmh,
            bearing_deg=r.bearing_deg,
            cell_id=r.cell_id,
            signal_strength_dbm=r.signal_strength_dbm,
            sensors=sens
        )
        latest_status = edge_engine.ingest_edge_report(report)
        processed += 1

    return {
        "status": "success",
        "processed_reports_count": processed,
        "train_number": batch.train_number,
        "latest_consensus_status": {
            "track_chainage_km": latest_status.track_chainage_km if latest_status else 0.0,
            "nearest_station": latest_status.nearest_station if latest_status else "UNKNOWN",
            "distance_to_station_km": latest_status.distance_to_station_km if latest_status else 0.0,
            "consensus_speed_kmh": latest_status.consensus_speed_kmh if latest_status else 0.0,
            "in_train_confidence_pct": latest_status.in_train_confidence_pct if latest_status else 0.0
        }
    }


@app.get("/api/v1/telemetry/edge_status/{train_number}")
def get_edge_train_status(train_number: str):
    """
    Returns live crowdsourced edge location consensus for a specific train service.
    """
    clean_no = str(train_number).strip().lstrip("0")
    consensus = edge_engine.compute_train_consensus(clean_no)
    return {
        "status": "success",
        "train_number": consensus.train_number,
        "last_updated_utc": consensus.last_updated_utc,
        "consensus_coordinates": {
            "latitude": consensus.consensus_lat,
            "longitude": consensus.consensus_lng
        },
        "consensus_speed_kmh": consensus.consensus_speed_kmh,
        "track_chainage_km": consensus.track_chainage_km,
        "nearest_station": consensus.nearest_station,
        "distance_to_station_km": consensus.distance_to_station_km,
        "cross_track_error_m": consensus.cross_track_error_m,
        "in_train_confidence_pct": consensus.in_train_confidence_pct,
        "motion_classification": consensus.motion_classification,
        "active_edge_devices": consensus.active_edge_devices_count,
        "primary_location_source": consensus.primary_location_source,
        "matched_corridor": consensus.matched_corridor,
        "is_halted": consensus.is_halted
    }


@app.get("/api/v1/telemetry/cell_towers")
def list_calibrated_cell_towers(corridor: Optional[str] = None):
    """
    Returns the master catalog of calibrated railway cellular base stations
    for client offline synchronization.
    """
    towers = []
    for cell_id, info in CALIBRATED_CELL_TOWERS.items():
        if corridor and info.get("zone") != corridor.upper():
            continue
        towers.append({
            "cell_id": cell_id,
            "latitude": info["lat"],
            "longitude": info["lng"],
            "station_code": info["station"],
            "description": info["description"],
            "accuracy_radius_meters": info["accuracy_m"],
            "operational_zone": info["zone"]
        })
    return {
        "status": "success",
        "total_calibrated_towers": len(towers),
        "towers": towers
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)

