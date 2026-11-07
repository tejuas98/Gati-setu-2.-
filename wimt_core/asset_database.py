"""
Where Is My Train Offline Asset Database Manager
Directly queries the offline SQLite databases and rake formation assets
extracted from Where Is My Train APK (com.whereismytrain.android).
"""

import os
import sqlite3
import zipfile
import tempfile
from typing import Dict, Any, List, Optional


class WIMTAssetDatabase:
    DEFAULT_APK = os.path.expanduser("~/Downloads/com.whereismytrain.android_7.1.5.974952539.apk")

    def __init__(self, apk_path: Optional[str] = None):
        self.apk_path = apk_path or self.DEFAULT_APK
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._temp_dir.name, "whereismytrain.db")
        self._extract_database()

    def _extract_database(self):
        with zipfile.ZipFile(self.apk_path, "r") as z:
            db_bytes = z.read("assets/databases/whereismytrain.db")
            with open(self._db_path, "wb") as f:
                f.write(db_bytes)

    def close(self):
        if self._temp_dir:
            self._temp_dir.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_train_info(self, train_number: str) -> Optional[Dict[str, Any]]:
        """Queries 13,550 trains in whereismytrain.db."""
        clean_no = str(train_number).strip().lstrip("0")
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT train_no, train_name, train_type, classes, speed_type
            FROM train_info
            WHERE train_no = ? OR train_no = ?
        """, (clean_no, clean_no.zfill(5)))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None
        return {
            "train_no": row[0],
            "train_name": row[1],
            "train_type": row[2],
            "classes_bitmask": row[3],
            "speed_type": row[4]
        }

    def get_station_info(self, station_code: str) -> Optional[Dict[str, Any]]:
        """Queries 10,083 Indian stations in whereismytrain.db."""
        stn = str(station_code).upper().strip()
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT station_code, title, lat, lng, wifi_station, city, place_id
            FROM station_info
            WHERE station_code = ?
        """, (stn,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None
        return {
            "station_code": row[0],
            "title": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "has_wifi": bool(row[4] == 1),
            "city": row[5],
            "google_place_id": row[6]
        }

    def get_rake_formation(self, train_number: str) -> Optional[Dict[str, Any]]:
        """Extracts exact coach formation from assets/train_info/coach_positions.txt."""
        target = str(train_number).strip().zfill(5)
        alt_target = str(train_number).strip().lstrip("0")

        with zipfile.ZipFile(self.apk_path, "r") as z:
            content = z.read("assets/train_info/coach_positions.txt").decode("utf-8", errors="ignore")
            for line in content.splitlines():
                if not line.strip():
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    t_no = parts[0].strip()
                    if t_no == target or t_no == alt_target:
                        coaches = [c.strip() for c in parts[3].split(",") if c.strip()]
                        is_lhb = "LHB" in parts[1].upper()
                        return {
                            "train_no": t_no,
                            "rake_type": parts[1].strip(),
                            "is_lhb": is_lhb,
                            "coach_count": len(coaches),
                            "coaches": coaches,
                            "raw_formation": parts[3].strip()
                        }
        return None

    def get_platform(self, station_code: str) -> str:
        """Extracts default platform lines from assets/train_info/kodu."""
        target = str(station_code).upper().strip()
        with zipfile.ZipFile(self.apk_path, "r") as z:
            content = z.read("assets/train_info/kodu").decode("utf-8", errors="ignore")
            for line in content.splitlines():
                if line.startswith(f"{target}|"):
                    _, platforms = line.split("|", 1)
                    pfs = [p.strip() for p in platforms.split(",") if p.strip()]
                    return pfs[0] if pfs else "1"
        return "1"

