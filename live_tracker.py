"""
Unified Multi-Source Train Tracker CLI
Integrates and cross-references live railway telemetry from:
1. RailRadar (api.railradar.in) - Open Next.js application gateway
2. RailJournal (radar.railjournal.in & media.railjournal.in) - Locomotive telemetry & WTT
3. Where Is My Train (Google / Sigmoid Labs) - Offline database, coach compositions & platforms

Usage:
  python3 live_tracker.py <train_number>
  python3 live_tracker.py 12951
"""

import sys
import os
import json
from datetime import datetime

# Import reverse engineered clients
from railradar_client import RailRadarClient
from railjournal_client import RailJournalClient
from whereismytrain_extractor import WhereIsMyTrainExtractor


def format_header(title: str, width: int = 70) -> str:
    line = "=" * width
    return f"\n{line}\n  {title}\n{line}"

def format_sub_header(title: str, width: int = 70) -> str:
    line = "-" * width
    return f"\n{line}\n  {title}\n{line}"


def track_train(train_number: str):
    clean_no = str(train_number).strip()
    print(format_header(f"GATI-SETU / SIH 2026: MULTI-SOURCE TELEMETRY TRACKER [{clean_no}]"))
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Query RailRadar
    print("\n[1/3] Querying RailRadar API gateway...")
    rr_client = RailRadarClient()
    rr_live = rr_client.get_live_status(clean_no)
    rr_data = rr_live.get("data") if rr_live.get("success") else None

    # 2. Query RailJournal
    print("[2/3] Querying RailJournal Onboard & Locomotive Telemetry...")
    rj_client = RailJournalClient()
    rj_live = rj_client.get_realtime_status(clean_no)
    rj_marker = rj_client.find_marker(clean_no)
    rj_wtt = rj_client.get_working_timetable(clean_no)

    # 3. Query Where Is My Train Offline Extractor
    print("[3/3] Querying Where Is My Train Local Database & Rake Rules...")
    wimt_meta = None
    wimt_rake = None
    wimt_platforms = []
    try:
        with WhereIsMyTrainExtractor() as extractor:
            search_res = extractor.search_train(clean_no)
            if search_res:
                wimt_meta = search_res[0]
            wimt_rake = extractor.get_coach_composition(clean_no)
            # Find destination or primary station platforms
            if rr_data and "destination" in rr_data:
                dest_code = rr_data["destination"].get("stationCode", "")
                wimt_platforms = extractor.get_station_platforms(dest_code)
    except Exception as e:
        print(f"  Note: WhereIsMyTrain local extraction warning: {e}")

    # ==========================
    # DISPLAY UNIFIED DASHBOARD
    # ==========================
    print(format_header("TELEMETRY CROSS-REFERENCE SUMMARY"))

    # Train Name & Type
    train_name = "Unknown"
    train_type = "Unknown"
    if rr_data:
        train_name = rr_data.get("trainName", train_name)
        train_type = rr_data.get("trainType", train_type)
    elif rj_live and rj_live.get("status"):
        train_name = rj_live.get("train_name", train_name)
        train_type = rj_live.get("train_sub_type", train_type)
    elif wimt_meta:
        train_name = wimt_meta.get("train_name", train_name)
        train_type = wimt_meta.get("train_type", train_type)

    print(f"Train: {clean_no} - {train_name} [{train_type}]")

    # Multi-source Running Status
    print(format_sub_header("REAL-TIME RUNNING STATUS & SPEED"))
    
    # RailRadar metrics
    if rr_data:
        delay = rr_data.get("delayMinutes", 0)
        status_txt = rr_data.get("status", "running")
        cur_loc = rr_data.get("currentLocation", {}).get("stationName", "En Route")
        speed = rr_data.get("speedKmh", "N/A")
        print(f"RailRadar:")
        print(f"  - Status: {status_txt}")
        print(f"  - Current Location: {cur_loc}")
        print(f"  - Delay: {delay} minutes")
        print(f"  - Speed: {speed} km/h")
        if "nextHalt" in rr_data:
            next_h = rr_data["nextHalt"]
            print(f"  - Next Halt: {next_h.get('stationName')} ({next_h.get('stationCode')})")
    else:
        print(f"RailRadar: No live run data available for {clean_no}")

    # RailJournal metrics
    if rj_live and rj_live.get("status"):
        loco_no = rj_live.get("loco_no", "Unassigned")
        loco_speed = rj_live.get("loco_speed", "0")
        loc_src = rj_live.get("location_source", "Unknown")
        gps_lat = rj_live.get("gps_latitude")
        gps_lon = rj_live.get("gps_longitude")
        gps_time = rj_live.get("gps_recv_datetime")
        print(f"RailJournal:")
        print(f"  - Attached Locomotive: #{loco_no} ({'Attached' if rj_live.get('loco_attached') else 'Detached'})")
        print(f"  - Locomotive Speed: {loco_speed} km/h")
        print(f"  - Telemetry Source: {loc_src}")
        print(f"  - Live GPS Coordinates: ({gps_lat}, {gps_lon})")
        print(f"  - GPS Packet Timestamp: {gps_time}")
        if rj_wtt and rj_wtt.get("status"):
            print(f"  - Operational Working Time Table (WTT): {rj_wtt.get('count')} section blocks")
    elif rj_marker:
        print(f"RailJournal Marker Feed:")
        print(f"  - Coords: ({rj_marker.get('lat')}, {rj_marker.get('lon')})")
        print(f"  - Traction Power: {'Electric' if rj_marker.get('power') == 'E' else 'Diesel'}")
        print(f"  - Projected Speed: {rj_marker.get('projection_speed_kmh')} km/h ({rj_marker.get('projection_source')})")
    else:
        print(f"RailJournal: No active marker found for {clean_no}")

    # Where Is My Train Coach & Platform Composition
    print(format_sub_header("WHERE IS MY TRAIN: RAKE & PLATFORM COMPOSITION"))
    if wimt_rake:
        print(f"Rake Type: {wimt_rake.get('rake_type')}")
        print(f"Total Coaches: {wimt_rake.get('coach_count')}")
        print(f"Coach Formation Order:")
        print(f"  {' -> '.join(wimt_rake.get('coaches', []))}")
    else:
        print("Rake Formation: Not indexed in local coach rules")

    if wimt_platforms:
        print(f"Default Platforms at Destination: {', '.join(wimt_platforms)}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    target_train = "12951"
    if len(sys.argv) > 1:
        target_train = sys.argv[1]
    track_train(target_train)

