"""
Automated Test Suite: Station Displays & Control Room Dashboards
Problem Statement ID: 26028 | Ministry of Railways | Smart India Hackathon 2026

Validates:
1. Passenger Information Display System (PIDS) Feed Formatting & Dual STA vs Dynamic ETA
2. Platform Allocation Conflict Detection & Automatic Reallocation Alerts
3. Section Controller Feed, Spatial Headway, Signal Aspects & Loop Line Precedence Advisor
4. Control Room Web Dashboards & PIDS Terminal HTML Availability
5. Weather and Safety Advisory Announcements
6. Junction Bottleneck Choke Identification (CNB, GZB, DDU vs NDLS)
"""

import os
import sys
import unittest
import requests

# Ensure project root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestStationDisplaysAndControlRoom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_pids_payload_formatting(self):
        """Verifies PIDS feed schema, dual STA/Dynamic ETA formatting, and platform metadata."""
        try:
            r = requests.get(f"{self.api_base}/api/v1/pids/NDLS", timeout=15)
            self.assertEqual(r.status_code, 200)
            data = r.json()

            self.assertEqual(data["status"], "success")
            self.assertEqual(data["station_code"], "NDLS")
            self.assertIn("station_name", data)
            self.assertIn("total_inbound_trains", data)
            self.assertIn("platform_conflicts_count", data)
            self.assertIn("announcement", data)
            self.assertIn("trains", data)

            if data["trains"]:
                first = data["trains"][0]
                self.assertIn("train_number", first)
                self.assertIn("train_name", first)
                self.assertIn("service_category", first)
                self.assertIn("scheduled_time", first)
                self.assertIn("dynamic_eta_time", first)
                self.assertIn("assigned_platform", first)
                self.assertIn("platform_conflict_detected", first)
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")

    def test_02_pids_platform_conflict_detection(self):
        """Verifies platform collision logic when multiple trains arrive within 15 min buffer."""
        try:
            r = requests.get(f"{self.api_base}/api/v1/pids/NDLS", timeout=15)
            self.assertEqual(r.status_code, 200)
            data = r.json()

            conflicts = [t for t in data.get("trains", []) if t.get("platform_conflict_detected")]
            if conflicts:
                first_conflict = conflicts[0]
                self.assertTrue(first_conflict["platform_conflict_detected"])
                self.assertIsNotNone(first_conflict["conflicting_train"])
                self.assertIn("RE-ALLOCATE PLATFORM", first_conflict["action_recommendation"])
                self.assertIn("ATTENTION:", data["announcement"])
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")

    def test_03_section_controller_feed_and_precedence_advisor(self):
        """Verifies Section Controller feed, headway tracking, and loop line precedence advice."""
        try:
            r = requests.get(f"{self.api_base}/api/v1/controller/section/CNB", timeout=15)
            self.assertEqual(r.status_code, 200)
            data = r.json()

            self.assertEqual(data["status"], "success")
            self.assertEqual(data["section_code"], "CNB")
            self.assertGreaterEqual(data["active_trains_count"], 1)
            self.assertIn("trains_in_section", data)

            first_train = data["trains_in_section"][0]
            self.assertIn("train_number", first_train)
            self.assertIn("spatial_headway_km", first_train)
            self.assertIn("signal_aspect", first_train)

            # Validate valid 4-aspect signal nomenclature
            valid_aspects = ["CLEAR_GREEN", "ATTENTION_DOUBLE_YELLOW", "CAUTION_SINGLE_YELLOW", "DANGER_RED"]
            self.assertIn(first_train["signal_aspect"], valid_aspects)
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")

    def test_04_html_dashboard_pages_availability(self):
        """Verifies HTTP 200 rendering for all public display and control room HTML views."""
        try:
            # 1. Section Controller Command Dashboard
            r_dash = requests.get(f"{self.api_base}/dashboard", timeout=10)
            self.assertEqual(r_dash.status_code, 200)
            self.assertIn("SECTION CONTROLLER & RADAR DESK", r_dash.text)
            self.assertIn("precedenceAdvisorCard", r_dash.text)

            # 2. Station PIDS Display
            r_pids = requests.get(f"{self.api_base}/pids", timeout=10)
            self.assertEqual(r_pids.status_code, 200)
            self.assertIn("PASSENGER INFORMATION DISPLAY SYSTEM", r_pids.text)
            self.assertIn("led-board", r_pids.text)

            # 3. Station Specific PIDS Display (NDLS)
            r_pids_ndls = requests.get(f"{self.api_base}/pids/NDLS", timeout=10)
            self.assertEqual(r_pids_ndls.status_code, 200)
            self.assertIn("NDLS", r_pids_ndls.text)

            # 4. Where Is My Train Interactive Application
            r_wimt = requests.get(f"{self.api_base}/wimt", timeout=10)
            self.assertEqual(r_wimt.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")

    def test_05_junction_bottleneck_choke_identification(self):
        """Verifies accurate categorization of high-friction diamond junctions as CONGESTED."""
        try:
            # High-density junction: Kanpur Central (CNB)
            r_cnb = requests.get(f"{self.api_base}/api/v1/controller/section/CNB", timeout=15)
            self.assertEqual(r_cnb.status_code, 200)
            d_cnb = r_cnb.json()
            self.assertEqual(d_cnb["bottleneck_weight"], 14.5)
            self.assertEqual(d_cnb["bottleneck_status"], "CONGESTED")

            # Standard terminal station: New Delhi (NDLS)
            r_ndls = requests.get(f"{self.api_base}/api/v1/controller/section/NDLS", timeout=15)
            self.assertEqual(r_ndls.status_code, 200)
            d_ndls = r_ndls.json()
            self.assertEqual(d_ndls["bottleneck_weight"], 8.0)
            self.assertEqual(d_ndls["bottleneck_status"], "NORMAL")
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")


if __name__ == "__main__":
    unittest.main()
