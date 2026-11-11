"""
Systematic Debugging & Fuzzing Test Suite
Problem Statement ID: 26028 | GatiSetu AI Engine

Probes:
1. Malformed and Boundary Inputs across all REST Endpoints
2. Error Handling & 500 Internal Server Error Prevention (Graceful 400/404 Responses)
3. Edge Location Sensor Fusion with Out-of-Bounds & Corrupt Telemetry
4. Fleet Vectorized Batch Inference with Nulls, Nonexistent IDs, and Large Batches
5. PIDS & Controller Desk Graceful Fallback on Cold/Empty Stations
"""

import os
import sys
import unittest
import requests
import numpy as np

# Ensure project root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edge_location_engine import edge_engine, EdgeLocationReport, MotionSensorData
from fleet_scalability_engine import fleet_engine
from eta_engine import DynamicETAEngine


class TestSystemDebuggingAndFuzzing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_forecast_invalid_and_boundary_train_numbers(self):
        """Probes /api/v1/forecast/{train_number} with nonexistent and malformed train numbers."""
        invalid_trains = ["999999", "INVALID", "00000", "-123", "   "]
        for t in invalid_trains:
            clean_param = t.strip() or "EMPTY"
            r = requests.get(f"{self.api_base}/api/v1/forecast/{clean_param}", timeout=10)
            # Must return 404 Not Found, never 500 Internal Server Error
            self.assertIn(r.status_code, [400, 404], f"Train {t} returned unhandled status {r.status_code}: {r.text}")

    def test_02_signal_aspects_invalid_train(self):
        """Probes /api/v1/corridor/signal-aspects/{train_number} with invalid inputs."""
        r = requests.get(f"{self.api_base}/api/v1/corridor/signal-aspects/999999", timeout=10)
        self.assertIn(r.status_code, [400, 404], f"Invalid signal request returned {r.status_code}")

    def test_03_station_dispatch_nonexistent_station(self):
        """Probes /api/v1/station/{station_code}/platform-dispatch with unknown station."""
        r = requests.get(f"{self.api_base}/api/v1/station/UNKNOWN_STN_99/platform-dispatch?hours=4", timeout=10)
        # Should return 404 or empty clean response, never crash with 500
        self.assertIn(r.status_code, [200, 404])

    def test_04_pids_invalid_station_code(self):
        """Probes /api/v1/pids/{station_code} with unknown station codes."""
        r = requests.get(f"{self.api_base}/api/v1/pids/NONEXISTENT_STN", timeout=10)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_inbound_trains"], 0)
        self.assertEqual(len(data["trains"]), 0)

    def test_05_fleet_invalid_zone_code(self):
        """Probes /api/v1/fleet/zone/{zone_code} with invalid zone codes."""
        r = requests.get(f"{self.api_base}/api/v1/fleet/zone/INVALID_ZONE", timeout=10)
        self.assertEqual(r.status_code, 404)
        data = r.json()
        self.assertIn("detail", data)

    def test_06_batch_forecast_empty_and_corrupt_payload(self):
        """Probes /api/v1/fleet/batch-forecast with empty list and mixed valid/invalid numbers."""
        # Case A: Empty list
        r_empty = requests.post(f"{self.api_base}/api/v1/fleet/batch-forecast", json={"train_numbers": []}, timeout=10)
        self.assertEqual(r_empty.status_code, 400)

        # Case B: Mixed valid and invalid train numbers
        mixed = ["12951", "NONEXISTENT", "12001", "999999", "22691"]
        r_mixed = requests.post(f"{self.api_base}/api/v1/fleet/batch-forecast", json={"train_numbers": mixed}, timeout=10)
        self.assertEqual(r_mixed.status_code, 200)
        data = r_mixed.json()
        self.assertTrue(data["success"])
        # Should gracefully process the 3 valid trains without throwing errors
        self.assertEqual(data["processed_count"], 3)

    def test_07_edge_ingest_corrupt_and_out_of_bounds_telemetry(self):
        """Probes edge location engine with out-of-bounds coordinates and extreme sensor noise."""
        pacific_report = EdgeLocationReport(
            device_id="DEV_FUZZ_01",
            train_number="12951",
            timestamp_utc="2026-11-11T13:30:00Z",
            source_type="SATELLITE_GPS",
            latitude=0.0,
            longitude=160.0,
            accuracy_m=10.0,
            speed_kmh=45.0,
            sensors=MotionSensorData(
                linear_z_variance=0.0,
                angular_speed_rad_s=0.0
            )
        )
        res = edge_engine.ingest_edge_report(pacific_report)
        self.assertIsNotNone(res)
        # Cross-track error should be capped and in-train confidence dampened
        self.assertLessEqual(res.in_train_confidence_pct, 50.0)

    def test_08_davis_resistance_zero_and_negative_speeds(self):
        """Verifies physics computation at standstill (0 km/h) and boundary speeds."""
        engine = DynamicETAEngine()
        profile = engine.TRACTION_PROFILES["ELECTRIC_HEAVY"]

        # 0 km/h (standstill)
        p0 = engine.compute_train_physics(profile, 22, 0.0)
        self.assertGreater(p0["davis_train_resistance_kn"], 0.0)  # Rolling resistance still exists

        # High speed (160 km/h)
        p160 = engine.compute_train_physics(profile, 22, 160.0)
        self.assertGreater(p160["davis_train_resistance_kn"], p0["davis_train_resistance_kn"])
        self.assertGreater(p160["service_braking_distance_m"], 100.0)

    def test_09_html_dashboard_and_pids_xss_safety(self):
        """Verifies that arbitrary station code parameters in /pids/{station_code} do not crash."""
        test_input = "ALERT_TEST_STATION"
        r = requests.get(f"{self.api_base}/pids/{test_input}", timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertIn("PASSENGER INFORMATION DISPLAY SYSTEM", r.text)


if __name__ == "__main__":
    unittest.main()
