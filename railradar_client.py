"""
RailRadar (api.railradar.in) Reverse-Engineered Client
Reverse engineered from https://railradar.in and Next.js frontend chunks.
Uses the internal unauthenticated /app/v1/ application gateway.
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List, Optional

class RailRadarClient:
    BASE_URL = "https://api.railradar.in/app/v1"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://railradar.in/",
        "Origin": "https://railradar.in"
    }

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 6.0) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"
        
        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                return json.loads(err_body)
            except Exception:
                return {"success": False, "error": {"code": f"HTTP_{e.code}", "message": str(e)}}
        except Exception as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e)}}

    def get_live_status(self, train_number: str) -> Dict[str, Any]:
        """
        Fetch real-time live running status for a train.
        Returns current coordinates, delay, speed, previous/next halt, and station timetable.
        """
        return self._get(f"/trains/{train_number}/live")

    def get_train_details(self, train_number: str, halts_only: bool = True) -> Dict[str, Any]:
        """
        Fetch scheduled timetable, reversal stations, classes, and source/destination.
        """
        return self._get(f"/trains/{train_number}", {"haltsOnly": str(halts_only).lower()})

    def get_route_geometry(self, train_number: str, stops: bool = True) -> Dict[str, Any]:
        """
        Fetch actual track geometry as GeoJSON LineString coordinates.
        """
        return self._get(f"/trains/{train_number}/route", {"format": "geojson", "stops": str(stops).lower()})

    def get_station_live_board(self, station_code: str, hours: int = 4, include_intermediate: bool = True) -> Dict[str, Any]:
        """
        Fetch upcoming arrivals and departures for a station within the next N hours.
        """
        return self._get(f"/stations/{station_code.upper()}/live", {
            "hours": hours,
            "includeIntermediate": str(include_intermediate).lower()
        })

    def get_coaches(self, train_number: str) -> Dict[str, Any]:
        """
        Fetch complete coach rake configuration (e.g. ENG-SLRD-GEN-S1-S2-B1-A1-H1...).
        """
        return self._get(f"/trains/{train_number}/coaches")

    def get_trains_between(self, from_station: str, to_station: str, date: str) -> Dict[str, Any]:
        """
        Find all trains between two stations on a specific date (YYYY-MM-DD).
        """
        return self._get(f"/trains/between/{from_station.upper()}/{to_station.upper()}", {"date": date})

    def get_live_radar_map(self) -> List[Dict[str, Any]]:
        """
        Fetch nationwide live radar. Unpacks the compact 13-tuple array into structured objects.
        Tuple mapping (reverse-engineered from RailRadar vector protocol):
          [0]: trainNumber
          [1]: typeId (0: Vande Bharat, 1: Rajdhani, 2: SF, 3: Express, 4: Garib Rath, 5: Jan Shatabdi, 6: Suburban, 7: Passenger, 8: Special, 9: Other)
          [2]: statusCode (0: Running, 1: Rescheduled, 2: Diverted)
          [3]: latitude (float)
          [4]: longitude (float)
          [5]: headingDegrees (float 0.0 to 360.0 bearing along rail track)
          [6]: delayMinutes (int signed minutes late/early)
          [7]: directionFlag (0: Down, 1: Up)
          [8]: statusFlag (1 = active)
          [9]: lastStationCode
          [10]: lastStationDistanceKm
          [11]: nextStationCode
          [12]: nextStationDistanceKm
        """
        raw = self._get("/live-map")
        if not raw.get("success") or "data" not in raw:
            return []
        
        parsed = []
        for t in raw["data"]:
            if len(t) >= 13:
                try:
                    heading_val = float(t[5])
                except (ValueError, TypeError):
                    heading_val = 0.0

                try:
                    delay_val = int(t[6])
                except (ValueError, TypeError):
                    delay_val = 0

                parsed.append({
                    "train_number": t[0],
                    "type_id": t[1],
                    "status_code": t[2],
                    "lat": float(t[3]),
                    "lng": float(t[4]),
                    "heading": heading_val,
                    "delay_minutes": delay_val,
                    "direction": t[7],
                    "is_active": bool(t[8]),
                    "last_station": t[9],
                    "last_station_dist_km": t[10],
                    "next_station": t[11],
                    "next_station_dist_km": t[12]
                })
        return parsed


if __name__ == "__main__":
    client = RailRadarClient()
    print("Testing RailRadar Client...")
    
    # Test 12951 (Mumbai Rajdhani)
    live = client.get_live_status("12951")
    if live.get("success"):
        data = live["data"]
        print(f"Train: {data['trainNumber']} - {data['trainName']}")
        print(f"Status: {data.get('status')}, Delay: {data.get('delayMinutes')} min")
        print(f"Current Location: {data.get('currentLocation', {}).get('stationName')}")
    else:
        print("Failed to fetch live train:", live.get("error"))

    # Test Live Radar
    trains = client.get_live_radar_map()
    print(f"Total Live Radar Trains across India: {len(trains)}")
    if trains:
        print("Sample Live Radar Train:", trains[0])

