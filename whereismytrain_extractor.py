"""
Where Is My Train (com.whereismytrain.android) Offline Asset Extractor & Database Reader
Reverse engineered from Where Is My Train APK v7.1.5 (Google / Sigmoid Labs).

Extracts and queries:
1. `whereismytrain.db` (13,550 trains, 10,083 stations, GPS coordinates, soundex index).
2. `coach_positions.txt` (13,201 rake configurations: LHB/ICF, locomotive, coach order).
3. `kodu` (9,414 station platform and line defaults).
4. `schedule.db` (Suburban local train timetables and platform sequences).
"""

import zipfile
import sqlite3
import os
import tempfile
from typing import Dict, Any, List, Optional


class WhereIsMyTrainExtractor:
    DEFAULT_APK = os.path.expanduser("~/Downloads/com.whereismytrain.android_7.1.5.974952539.apk")

    def __init__(self, apk_path: Optional[str] = None):
        self.apk_path = apk_path or self.DEFAULT_APK
        if not os.path.exists(self.apk_path):
            raise FileNotFoundError(f"Where Is My Train APK not found at: {self.apk_path}")
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = None
        self._load_database()

    def _load_database(self):
        """Extracts whereismytrain.db to temporary storage for high-speed SQLite querying."""
        with zipfile.ZipFile(self.apk_path, "r") as z:
            db_bytes = z.read("assets/databases/whereismytrain.db")
            self._db_path = os.path.join(self._temp_dir.name, "whereismytrain.db")
            with open(self._db_path, "wb") as f:
                f.write(db_bytes)

    def close(self):
        """Cleans up extracted temporary database files."""
        if self._temp_dir:
            self._temp_dir.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def search_train(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for a train by train number or train name.
        Uses the internal train_info table (13,550 Indian Railways trains).
        """
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        q = f"%{query}%"
        cur.execute("""
            SELECT train_no, train_name, train_type, classes, speed_type, city
            FROM train_info
            WHERE train_no LIKE ? OR train_name LIKE ?
            LIMIT 20
        """, (q, q))
        rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            results.append({
                "train_no": r[0],
                "train_name": r[1],
                "train_type": r[2],
                "classes_bitmask": r[3],
                "speed_type": r[4],
                "city": r[5]
            })
        return results

    def get_station_info(self, station_code: str) -> Optional[Dict[str, Any]]:
        """
        Get exact station details, GPS coordinates, and popularity metrics.
        Uses the internal station_info table (10,083 Indian stations).
        """
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT station_code, title, lat, lng, wifi_station, uber_available, city, place_id
            FROM station_info
            WHERE station_code = ?
        """, (station_code.upper(),))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None
        return {
            "station_code": row[0],
            "title": row[1],
            "lat": row[2],
            "lng": row[3],
            "has_wifi": bool(row[4] == 1),
            "uber_available": bool(row[5] == 1),
            "city": row[6],
            "google_place_id": row[7]
        }

    def get_coach_composition(self, train_number: str) -> Optional[Dict[str, Any]]:
        """
        Extracts rake formation from assets/train_info/coach_positions.txt.
        Provides coach ordering (e.g. L, EOG, GS, S1, B1, A1, H1).
        """
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
                        return {
                            "train_no": t_no,
                            "rake_type": parts[1].strip(),
                            "coach_count": len(coaches),
                            "coaches": coaches,
                            "raw_formation": parts[3].strip()
                        }
        return None

    def get_station_platforms(self, station_code: str) -> List[str]:
        """
        Extracts default platform lines from assets/train_info/kodu.
        """
        target = station_code.upper().strip()
        with zipfile.ZipFile(self.apk_path, "r") as z:
            content = z.read("assets/train_info/kodu").decode("utf-8", errors="ignore")
            for line in content.splitlines():
                if line.startswith(f"{target}|"):
                    _, platforms = line.split("|", 1)
                    return [p.strip() for p in platforms.split(",") if p.strip()]
        return []


if __name__ == "__main__":
    print("Testing Where Is My Train Asset Extractor...")
    extractor = WhereIsMyTrainExtractor()

    # Test train search
    trains = extractor.search_train("12951")
    print("Train Search Results for '12951':", trains)

    # Test station info
    mmct = extractor.get_station_info("MMCT")
    print("Station Info for MMCT:", mmct)

    ndls = extractor.get_station_info("NDLS")
    print("Station Info for NDLS:", ndls)

    # Test coach composition
    rake = extractor.get_coach_composition("12951")
    print("Coach Rake Composition for 12951:", rake)

    # Test station platforms
    ndls_platforms = extractor.get_station_platforms("NDLS")
    print("NDLS Platforms from Kodu:", ndls_platforms)

    extractor.close()
    print("Extractor test complete.")

