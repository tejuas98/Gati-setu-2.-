"""
RailJournal (railjournal.in) Reverse-Engineered Client
Reverse engineered from https://railjournal.in/Railradar.php

Endpoints exposed:
1. Real-time Train Markers Feed: https://media.railjournal.in/rail-data/markers/current-web.txt
2. Real-time Train Status & Loco Telemetry: https://radar.railjournal.in/api/check_train_info_realtime.php
3. ICMS / COA Working Time Table (WTT): https://railjournal.in/api/train_tt_full.php
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class RailJournalClient:
    MARKERS_URL = "https://media.railjournal.in/rail-data/markers/current-web.txt"
    REALTIME_URL = "https://radar.railjournal.in/api/check_train_info_realtime.php"
    TIMETABLE_URL = "https://railjournal.in/api/train_tt_full.php"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://railjournal.in/Railradar.php",
        "Origin": "https://railjournal.in",
        "Accept": "application/json, text/plain, */*"
    }

    def _get_json(self, url: str) -> Dict[str, Any]:
        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(body)
            except Exception:
                return {"status": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"status": False, "error": str(e)}

    def get_live_markers(self) -> Dict[str, Any]:
        """
        Fetch nationwide active train markers (~2,400+ running trains).
        Contains GPS/NTES telemetry, locomotive power (E/D), speed, and route track segments.
        """
        return self._get_json(self.MARKERS_URL)

    def find_marker(self, train_number: str) -> Optional[Dict[str, Any]]:
        """
        Search current nationwide markers for a specific train number.
        """
        data = self.get_live_markers()
        if not data.get("status") or "data" not in data:
            return None
        
        target = str(train_number).strip().lstrip("0")
        for item in data["data"]:
            item_no = str(item.get("train_no", "")).strip().lstrip("0")
            if item_no == target:
                return item
        return None

    def get_realtime_status(self, train_number: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch real-time locomotive and running status for a train.
        Parameters:
            train_number: e.g. "12951"
            start_date: format "DD-Mmm-YYYY" (e.g. "07-Nov-2026"). Defaults to today.
        Returns:
            Locomotive number, speed, exact GPS lat/lon, delay status, and public schedule.
        """
        if not start_date:
            start_date = datetime.now().strftime("%d-%b-%Y")
        
        query = urllib.parse.urlencode({
            "trainNo": train_number,
            "startDate": start_date,
            "v": "2"
        })
        url = f"{self.REALTIME_URL}?{query}"
        return self._get_json(url)

    def get_working_timetable(self, train_number: str, start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch Indian Railways internal ICMS/COA Working Time Table (WTT).
        Includes operational stops, technical passes, platforms, divisions, and railway zones.
        """
        if not start_date:
            start_date = datetime.now().strftime("%d-%b-%Y")
        
        query = urllib.parse.urlencode({
            "trainNo": train_number,
            "startDate": start_date
        })
        url = f"{self.TIMETABLE_URL}?{query}"
        return self._get_json(url)


if __name__ == "__main__":
    client = RailJournalClient()
    print("Testing RailJournal Client...")

    # 1. Fetch markers
    markers_resp = client.get_live_markers()
    print(f"Total Active RailJournal Markers: {markers_resp.get('count')}")

    # 2. Query real-time status of 12951
    live = client.get_realtime_status("12951")
    if live.get("status"):
        print(f"Train: {live.get('train_no')} - {live.get('train_name')}")
        print(f"Locomotive Attached: {live.get('loco_attached')}, Loco No: {live.get('loco_no')}")
        print(f"Loco Speed: {live.get('loco_speed')} km/h, Location: {live.get('current_location')}")
        print(f"GPS Coordinates: ({live.get('gps_latitude')}, {live.get('gps_longitude')})")
        print(f"Location Source: {live.get('location_source')}")
    else:
        print("Realtime status error:", live.get("error"))

    # 3. Query WTT stops
    wtt = client.get_working_timetable("12951")
    if wtt.get("status"):
        print(f"Operational WTT Blocks/Stops count: {wtt.get('count')}")
        print(f"Data source: {wtt.get('source')}")

