"""
Automated Test Suite: Fleet-Wide Scalability Engine (13,000+ Coaching Trains)
Problem Statement ID: 26028 | Ministry of Railways | Smart India Hackathon 2026

Validates:
1. Full Fleet Dataset Integrity (13,550 trains with complete operational telemetry)
2. All 18 Indian Railways Operational Zones Partitioning & Coverage
3. Vectorized Batch Dynamic Forecasting & Monotonic Quantile Bounds (P10 <= P50 <= P90)
4. High-Throughput Stress Testing (> 5,000 trains/sec, sub-millisecond latency)
5. Memory Footprint Efficiency (RAM <= 200 MB for entire national fleet)
6. Zonal Punctuality and Anomaly Aggregations
7. Live HTTP REST API Integration on Port 8000
"""

import os
import sys
import unittest
import time
import psutil
import requests

# Ensure project root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fleet_scalability_engine import FleetScalabilityEngine, fleet_engine


class TestFleetScalability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = fleet_engine
        cls.api_base = "http://127.0.0.1:8000"

    def test_01_fleet_dataset_integrity(self):
        """Verifies full fleet integrity covering exactly 13,550 Indian Railways trains."""
        self.assertEqual(self.engine.total_trains, 13550)
        self.assertGreaterEqual(len(self.engine.train_lookup), 13500)

        # Validate essential operational attributes in sample records
        sample = self.engine.train_lookup.get("12951") or self.engine.train_lookup.get("12001")
        self.assertIsNotNone(sample)
        self.assertIn("train_name", sample)
        self.assertIn("service_category", sample)
        self.assertIn("operational_zone", sample)
        self.assertIn("current_delay_min", sample)
        self.assertIn("speed_cap_kmh", sample)

    def test_02_18_operational_zones_partitioning(self):
        """Verifies that all 18 Indian Railways operational zones are populated and balanced."""
        expected_zones = [
            "NR", "WR", "CR", "ER", "SR", "SCR", "SER", "ECR",
            "NCR", "NWR", "SWR", "WCR", "ECOR", "NFR", "NER",
            "SECR", "KR", "MR"
        ]
        summary = self.engine.get_fleet_summary()
        self.assertEqual(summary["operational_zones_covered"], 18)

        zone_breakdown = summary["zone_breakdown"]
        for z in expected_zones:
            self.assertIn(z, zone_breakdown, f"Missing operational zone: {z}")
            self.assertGreater(zone_breakdown[z]["total_trains"], 0, f"Zone {z} has 0 trains assigned")
            self.assertIn("punctuality_rate_pct", zone_breakdown[z])
            self.assertIn("primary_divisions", zone_breakdown[z])

    def test_03_vectorized_batch_forecasting_accuracy(self):
        """Verifies vectorized batch forecasting math and strictly monotonic quantile intervals."""
        test_numbers = ["12951", "12001", "12301", "22691", "18309", "18102"]
        result = self.engine.batch_forecast_eta(test_numbers)

        self.assertTrue(result["success"])
        self.assertEqual(result["processed_count"], len(test_numbers))
        self.assertGreater(result["throughput_trains_per_sec"], 500.0)

        for fc in result["forecasts"]:
            ci = fc["confidence_interval"]
            p10 = ci["p10_optimistic_delay_min"]
            p50 = ci["p50_expected_delay_min"]
            p90 = ci["p90_pessimistic_delay_min"]

            # Mathematical monotonicity: P10 <= P50 <= P90
            self.assertLessEqual(p10, p50 + 1e-4, f"Violated P10 <= P50 for train {fc['train_no']}")
            self.assertLessEqual(p50, p90 + 1e-4, f"Violated P50 <= P90 for train {fc['train_no']}")
            self.assertIn(fc["zone"], self.engine.ZONE_METADATA)

    def test_04_throughput_stress_benchmark(self):
        """Verifies high-throughput stress capability exceeding 5,000 trains/sec."""
        bench = self.engine.benchmark_fleet_throughput(sample_size=1000)

        self.assertEqual(bench["sample_size_trains"], 1000)
        self.assertGreater(bench["throughput_trains_per_second"], 5000.0)
        self.assertLess(bench["mean_inference_latency_per_train_ms"], 0.20)
        # Full national fleet 13,550 trains must be computable in under 3.0 seconds
        self.assertLess(bench["full_fleet_13550_projected_time_ms"], 3000.0)

    def test_05_memory_footprint_and_efficiency(self):
        """Verifies that the entire 13,550 train fleet index operates within strict RAM limits (<= 200 MB)."""
        proc = psutil.Process()
        mem_rss_mb = proc.memory_info().rss / (1024.0 * 1024.0)
        self.assertLess(mem_rss_mb, 200.0, f"Memory footprint exceeded limit: {mem_rss_mb} MB")

    def test_06_zonal_punctuality_and_metrics(self):
        """Verifies zonal aggregation metrics, average delays, and punctuality rates."""
        summary = self.engine.get_fleet_summary()
        self.assertGreaterEqual(summary["fleet_punctuality_rate_pct"], 60.0)
        self.assertLessEqual(summary["fleet_punctuality_rate_pct"], 100.0)
        self.assertGreater(summary["fleet_mean_delay_min"], 0.0)

        # Test specific zone retrieval (Western Railway)
        wr_data = self.engine.get_zone_fleet("WR", limit=50)
        self.assertTrue(wr_data["success"])
        self.assertEqual(wr_data["zone_code"], "WR")
        self.assertGreater(wr_data["total_zone_trains"], 1000)
        self.assertEqual(wr_data["returned_count"], 50)

    def test_07_live_api_fleet_endpoints(self):
        """Verifies HTTP API integration on port 8000 for all fleet-wide scalability endpoints."""
        try:
            # 1. Fleet Status Endpoint
            r_stat = requests.get(f"{self.api_base}/api/v1/fleet/status", timeout=10)
            self.assertEqual(r_stat.status_code, 200)
            d_stat = r_stat.json()
            self.assertEqual(d_stat["fleet_size"], 13550)
            self.assertEqual(d_stat["operational_zones_covered"], 18)

            # 2. Zone Filter Endpoint
            r_zone = requests.get(f"{self.api_base}/api/v1/fleet/zone/NR?limit=10", timeout=10)
            self.assertEqual(r_zone.status_code, 200)
            d_zone = r_zone.json()
            self.assertEqual(d_zone["zone_code"], "NR")
            self.assertEqual(d_zone["returned_count"], 10)

            # 3. Batch Forecast Endpoint
            payload = {"train_numbers": ["12951", "12001", "12301", "22691"]}
            r_batch = requests.post(f"{self.api_base}/api/v1/fleet/batch-forecast", json=payload, timeout=10)
            self.assertEqual(r_batch.status_code, 200)
            d_batch = r_batch.json()
            self.assertEqual(d_batch["processed_count"], 4)
            self.assertIn("forecasts", d_batch)

            # 4. Benchmark Endpoint
            r_bench = requests.get(f"{self.api_base}/api/v1/fleet/benchmark?sample_size=500", timeout=10)
            self.assertEqual(r_bench.status_code, 200)
            d_bench = r_bench.json()
            self.assertEqual(d_bench["sample_size_trains"], 500)
            self.assertGreater(d_bench["throughput_trains_per_second"], 5000.0)
        except requests.exceptions.ConnectionError:
            self.skipTest("API Server not reachable on port 8000")


if __name__ == "__main__":
    unittest.main()
