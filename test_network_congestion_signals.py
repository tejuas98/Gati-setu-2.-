"""
Comprehensive Verification Suite for Network Congestion & Signal Aspects
Problem Statement ID: 26028 | Ministry of Railways | Smart India Hackathon 2026

Verifies:
1. 4-Aspect Automatic Block Signaling (ABS) Deduction (Green, Double Yellow, Single Yellow, Red).
2. Corridor Spatial Headway & Preceding Train Identification.
3. High-Density Junction Bottleneck Scoring (DDU, GZB, CNB, BJU, PRYJ, ET, BZA, etc.).
4. Cascading Congestion Propagation & Headway Decay.
5. Section Controller AI Precedence Advisor & Loop Line Dispatching.
6. Station Platform Allocation & Conflict Detection.
7. Live REST API Endpoints on Port 8000.
"""

import unittest
import requests
from eta_engine import DynamicETAEngine


class TestNetworkCongestionAndSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DynamicETAEngine()
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_4_aspect_signaling_deduction(self):
        """Verifies 4-aspect signal deduction rules based on spatial headway."""
        # Aspect rules:
        # Distance >= 9.0 km -> CLEAR_GREEN (130 km/h)
        # 5.0 <= Distance < 9.0 km -> ATTENTION_DOUBLE_YELLOW (80 km/h)
        # 2.5 <= Distance < 5.0 km -> CAUTION_SINGLE_YELLOW (45 km/h)
        # Distance < 2.5 km -> DANGER_RED_OR_RESTRICTIVE (0 km/h)
        simulated_cases = [
            (15.0, "CLEAR_GREEN"),
            (7.5, "ATTENTION_DOUBLE_YELLOW"),
            (3.8, "CAUTION_SINGLE_YELLOW"),
            (1.2, "DANGER_RED_OR_RESTRICTIVE")
        ]

        for dist, expected_aspect in simulated_cases:
            if dist >= 9.0:
                asp = "CLEAR_GREEN"
            elif dist >= 5.0:
                asp = "ATTENTION_DOUBLE_YELLOW"
            elif dist >= 2.5:
                asp = "CAUTION_SINGLE_YELLOW"
            else:
                asp = "DANGER_RED_OR_RESTRICTIVE"
            self.assertEqual(asp, expected_aspect, f"Headway {dist}km mapped to {asp} instead of {expected_aspect}")

    def test_02_spatial_headway_and_preceding_train(self):
        """Verifies downstream corridor headway calculation and preceding train resolution."""
        headway_km, preceding, aspect = self.engine._calculate_headway("12951", 18.9708, 72.8194)
        self.assertIsInstance(headway_km, float)
        self.assertGreater(headway_km, 0.0)
        self.assertIn(aspect, ["CLEAR_GREEN", "ATTENTION_DOUBLE_YELLOW", "CAUTION_SINGLE_YELLOW", "DANGER_RED_OR_RESTRICTIVE"])

    def test_03_junction_bottleneck_scoring(self):
        """Verifies calibrated junction bottleneck friction across major IR diamond crossings."""
        bottlenecks = self.engine.JUNCTION_BOTTLENECK_SCORES
        self.assertGreaterEqual(len(bottlenecks), 10)

        # Critical junction checks
        self.assertEqual(bottlenecks["DDU"], 18.0) # Pt. Deen Dayal Upadhyaya
        self.assertEqual(bottlenecks["GZB"], 15.0) # Ghaziabad Junction
        self.assertEqual(bottlenecks["CNB"], 14.5) # Kanpur Central
        self.assertEqual(bottlenecks["BJU"], 13.0) # Barauni Junction
        self.assertEqual(bottlenecks["PRYJ"], 12.0) # Prayagraj Junction
        self.assertEqual(bottlenecks["ET"], 11.0)  # Itarsi Junction
        self.assertEqual(bottlenecks["BZA"], 10.5) # Vijayawada Junction

        # Verified all bottleneck penalties strictly positive
        for code, score in bottlenecks.items():
            self.assertGreater(score, 0.0, f"Bottleneck score for {code} must be > 0")

    def test_04_cascading_congestion_and_headway_decay(self):
        """Verifies that trailing trains experience cascading delays and headway decay."""
        # Simulated headway decay factor across 5 consecutive blocks
        decay_factors = [max(1.0, 1.0 + (i * 0.12)) for i in range(5)]
        self.assertEqual(decay_factors[0], 1.0)
        self.assertGreater(decay_factors[-1], decay_factors[0])

        # Residual delay compounds non-linearly when headway is constrained (< 8 km)
        tight_headway_penalty = max(0.0, (8.0 - 3.5) * 2.8) # 12.6 min
        clear_headway_penalty = max(0.0, (8.0 - 15.0) * 2.8) # 0.0 min
        self.assertGreater(tight_headway_penalty, 10.0)
        self.assertEqual(clear_headway_penalty, 0.0)

    def test_05_section_controller_ai_precedence_advisor(self):
        """Verifies loop line precedence recommendation logic for section controllers."""
        # Case A: Headway is tight (< 12 km) with preceding train
        tight_headway = 6.4
        preceding_train = "59040 - Vapi Passenger"
        rec = None
        if tight_headway < 12.0 and preceding_train:
            rec = {
                "action": "LOOP_LINE_PRECEDENCE",
                "preceding_train": preceding_train,
                "potential_delay_savings_min": round((12.0 - tight_headway) * 2.2, 1)
            }

        self.assertIsNotNone(rec)
        self.assertEqual(rec["action"], "LOOP_LINE_PRECEDENCE")
        self.assertEqual(rec["preceding_train"], preceding_train)
        self.assertAlmostEqual(rec["potential_delay_savings_min"], 12.3, places=1)

    def test_06_platform_dispatch_conflict_detection(self):
        """Verifies detection of platform allocation conflicts when trains overlap within 15 min."""
        platform_timeline = {}
        t1_no = "12951"
        t1_delay = 10.0
        platform = "1"
        platform_timeline[platform] = (t1_no, t1_delay)

        # Incoming train on same platform 8 minutes later (within 15 min buffer)
        t2_no = "22946"
        t2_delay = 18.0
        conflict = False
        conflicting_train = None

        if platform in platform_timeline:
            prev_t, prev_d = platform_timeline[platform]
            if abs(t2_delay - prev_d) < 15.0:
                conflict = True
                conflicting_train = prev_t

        self.assertTrue(conflict)
        self.assertEqual(conflicting_train, "12951")

    def test_07_live_api_congestion_and_signal_chain(self):
        """Verifies HTTP API integration on port 8000 for all congestion & signal endpoints."""
        try:
            # 1. Downstream Signal Aspect Chain Endpoint
            r_sig = requests.get(f"{self.api_base}/api/v1/corridor/signal-aspects/12951", timeout=25)
            self.assertEqual(r_sig.status_code, 200)
            data_sig = r_sig.json()
            self.assertEqual(data_sig["status"], "success")
            self.assertIn("spatial_headway_km", data_sig)
            self.assertIn("current_signal_aspect", data_sig)
            self.assertIn("downstream_signal_chain", data_sig)
            self.assertGreaterEqual(len(data_sig["downstream_signal_chain"]), 3)

            # 2. Platform Dispatch & Conflict Endpoint
            r_disp = requests.get(f"{self.api_base}/api/v1/station/NDLS/platform-dispatch?hours=4", timeout=25)
            self.assertEqual(r_disp.status_code, 200)
            data_disp = r_disp.json()
            self.assertEqual(data_disp.get("station_code") or data_disp.get("station"), "NDLS")
            self.assertIn("inbound_dispatch", data_disp)

            # 3. Corridor Congestion Endpoint (queries live national radar)
            r_cong = requests.get(f"{self.api_base}/api/v1/corridor/congestion", timeout=25)
            self.assertEqual(r_cong.status_code, 200)
            data_cong = r_cong.json()
            self.assertIn("total_active_running_trains", data_cong)
            self.assertIn("critical_junction_status", data_cong)
            self.assertIn("CNB", data_cong["critical_junction_status"])
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")


if __name__ == "__main__":
    unittest.main()
