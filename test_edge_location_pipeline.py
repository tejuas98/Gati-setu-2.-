"""
Comprehensive Edge Location Data Collection & Sensor Fusion Test Suite
Problem Statement ID: 26028 | Ministry of Railways | Smart India Hackathon 2026
"""

import sys
import unittest
import requests
from edge_location_engine import (
    EdgeLocationEngine,
    MotionSensorData,
    EdgeLocationReport,
    CALIBRATED_CELL_TOWERS
)


class TestEdgeLocationDataCollection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = EdgeLocationEngine()
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_cell_tower_triangulation(self):
        """Verifies on-device offline cellular base station resolution ({MCC}_{MNC}_{LAC}_{CID})."""
        # Test Mumbai Central Tower
        mmct = self.engine.resolve_cell_tower("404_45_1204_49182")
        self.assertIsNotNone(mmct)
        self.assertEqual(mmct["station_code"], "MMCT")
        self.assertEqual(mmct["operational_zone"], "WR")
        self.assertAlmostEqual(mmct["latitude"], 18.9708, places=3)
        self.assertAlmostEqual(mmct["longitude"], 72.8194, places=3)

        # Test New Delhi Terminal Tower
        ndls = self.engine.resolve_cell_tower("404_45_2901_11402")
        self.assertIsNotNone(ndls)
        self.assertEqual(ndls["station_code"], "NDLS")
        self.assertEqual(ndls["operational_zone"], "NR")

    def test_02_sensor_fusion_motion_classification(self):
        """Verifies harmonic vertical rail joint vibration vs road turning vehicle disambiguation."""
        # 1. Authentic rail coach: Harmonic rail joint vibration, smooth track curvature
        rail_coach = MotionSensorData(linear_z_variance=2.8, angular_speed_rad_s=0.04)
        m_class, conf = self.engine.classify_motion(rail_coach, speed_kmh=80.0)
        self.assertEqual(m_class, "IN_TRAIN")
        self.assertGreaterEqual(conf, 80.0)

        # 2. Highway road bus: Sharp 90-degree intersection turn
        road_bus = MotionSensorData(linear_z_variance=0.7, angular_speed_rad_s=0.48)
        m_class, conf = self.engine.classify_motion(road_bus, speed_kmh=55.0)
        self.assertEqual(m_class, "ROAD_VEHICLE")
        self.assertLess(conf, 30.0)

        # 3. Train halted at platform: Low vibration, near zero speed
        halted_train = MotionSensorData(linear_z_variance=0.15, angular_speed_rad_s=0.01)
        m_class, conf = self.engine.classify_motion(halted_train, speed_kmh=0.0)
        self.assertEqual(m_class, "STATIONARY_AT_PLATFORM")
        self.assertGreaterEqual(conf, 90.0)

    def test_03_track_centerline_snapping(self):
        """Verifies spatial projection onto Indian Railways track centerlines and kilometer posts."""
        # Test coordinate slightly offset from Surat Yard track
        lat, lng = 21.2052, 72.8415
        corridor, chainage, cross_track_m, nearest_stn, dist_stn = self.engine.snap_to_track_centerline(lat, lng)
        self.assertEqual(corridor, "MUMBAI_DELHI_MAIN")
        self.assertEqual(nearest_stn, "ST")
        self.assertLess(cross_track_m, 100.0)  # Cross-track error under 100 meters
        self.assertAlmostEqual(chainage, 263.5, delta=5.0)

    def test_04_crowdsourced_multi_device_consensus(self):
        """Verifies fusion of multiple passenger edge reports with weighted outlier dampening."""
        train_no = "12951"
        eng = EdgeLocationEngine()

        # Passenger A: GPS report
        rep_a = EdgeLocationReport(
            device_id="pax_a",
            train_number=train_no,
            timestamp_utc="2026-11-11T12:00:00Z",
            source_type="SATELLITE_GPS",
            latitude=28.6415,
            longitude=77.2205,
            accuracy_m=10.0,
            speed_kmh=0.0,
            sensors=MotionSensorData(linear_z_variance=0.1)
        )
        # Passenger B: Cell Tower report
        rep_b = EdgeLocationReport(
            device_id="pax_b",
            train_number=train_no,
            timestamp_utc="2026-11-11T12:00:02Z",
            source_type="CELL_TRIANGULATION",
            latitude=28.6418,
            longitude=77.2203,
            accuracy_m=150.0,
            speed_kmh=0.0,
            sensors=MotionSensorData(linear_z_variance=0.1)
        )

        eng.ingest_edge_report(rep_a)
        consensus = eng.ingest_edge_report(rep_b)

        self.assertEqual(consensus.active_edge_devices_count, 2)
        self.assertEqual(consensus.nearest_station, "NDLS")
        self.assertTrue(consensus.is_halted)
        self.assertAlmostEqual(consensus.consensus_lat, 28.6415, places=3)

    def test_05_live_api_edge_endpoints(self):
        """Verifies HTTP API integration of edge endpoints on running FastAPI server."""
        try:
            # Check cell towers
            r_towers = requests.get(f"{self.api_base}/api/v1/telemetry/cell_towers", timeout=3)
            self.assertEqual(r_towers.status_code, 200)
            data_towers = r_towers.json()
            self.assertEqual(data_towers["status"], "success")
            self.assertGreaterEqual(data_towers["total_calibrated_towers"], 30)

            # Ingest live edge packet
            payload = {
                "device_id": "integration_test_client",
                "train_number": "12951",
                "source_type": "SATELLITE_GPS",
                "latitude": 28.5889,
                "longitude": 77.2534,
                "accuracy_m": 12.0,
                "speed_kmh": 95.0,
                "sensors": {
                    "linear_z_variance": 2.4,
                    "angular_speed_rad_s": 0.03
                }
            }
            r_ingest = requests.post(f"{self.api_base}/api/v1/telemetry/edge_ingest", json=payload, timeout=3)
            self.assertEqual(r_ingest.status_code, 200)
            data_ingest = r_ingest.json()
            self.assertEqual(data_ingest["status"], "success")
            self.assertEqual(data_ingest["nearest_station"], "NZM")
            self.assertEqual(data_ingest["matched_corridor"], "MUMBAI_DELHI_MAIN")
            self.assertGreaterEqual(data_ingest["in_train_confidence_pct"], 80.0)

            # Query live consensus
            r_status = requests.get(f"{self.api_base}/api/v1/telemetry/edge_status/12951", timeout=3)
            self.assertEqual(r_status.status_code, 200)
            data_status = r_status.json()
            self.assertEqual(data_status["train_number"], "12951")
            self.assertEqual(data_status["nearest_station"], "NZM")
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")


if __name__ == "__main__":
    unittest.main()

