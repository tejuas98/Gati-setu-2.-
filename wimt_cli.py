"""
Where Is My Train (WIMT) Reverse-Engineered CLI
Runs Where Is My Train with Train Physics & Weather Speed Restrictions.

Usage:
  python3 wimt_cli.py <train_number>
  python3 wimt_cli.py 12951
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wimt_core.dynamic_eta_service import WIMTDynamicETAService


def run_cli(train_number: str = "12951"):
    service = WIMTDynamicETAService()
    print("=" * 80)
    print(f"  WHERE IS MY TRAIN (REVERSE-ENGINEERED) : DYNAMIC ETA & PHYSICS ENGINE")
    print(f"  Target Train: #{train_number}")
    print("=" * 80)

    report = service.get_dynamic_running_status(train_number)
    if not report.get("success"):
        print("Error:", report.get("message"))
        return

    print(f"\nTrain: {report['train_number']} - {report['train_name']} [{report['train_type']}]")
    print(f"Current Location: {report['current_location']} | Current Speed: {report['speed_kmh']} km/h")
    print(f"Locomotive Engine: #{report['locomotive_serial']}")

    # Print Physics
    phys = report["train_physics"]
    print("\n--- INSTANTANEOUS TRAIN DYNAMICS & PHYSICS ---")
    print(f"Locomotive Type:          {phys['locomotive_type']} ({phys['power_hp']} HP)")
    print(f"Continuous Tractive Effort: {phys['continuous_tractive_effort_kn']} kN")
    print(f"Davis Train Resistance:    {phys['davis_train_resistance_kn']} kN (Rolling + Flange + Aerodynamic)")
    print(f"Trailing Rake Mass:        {phys['trailing_rake_mass_tons']} tons ({phys['coach_count']} Coaches, {phys['rake_type']})")
    print(f"Total Train Mass:          {phys['total_train_mass_tons']} metric tons")
    print(f"Net Acceleration Rate:     {phys['net_acceleration_rate_m_s2']} m/s²")
    print(f"Service Braking Distance:  {phys['service_braking_distance_m']} meters")

    if report.get("coach_rake"):
        print(f"Coach Formation Order:     {' -> '.join(report['coach_rake'][:10])}...")

    # Print Station Comparison
    print("\n" + "=" * 80)
    print("  STATION-BY-STATION ETA: REPLACING OLD WIMT STATIC WITH GATI-SETU DYNAMIC")
    print("=" * 80)

    for stn in report.get("stations", [])[:6]:
        print(f"\n[{stn['station_code']}] {stn['station_name']} (Dist: {stn['distance_km']} km | PF: {stn['platform']})")
        print(f"  Weather Conditions:  {stn['weather_condition']} (Speed Cap: {stn['weather_speed_cap_kmh']} km/h)")
        print(f"  Scheduled Time (STA):{stn['scheduled_arrival_sta']}")
        print(f"  REPLACED Old Static: {stn['superseded_static_eta']} (Naive Delay: +{stn['superseded_static_delay_min']}m)")
        print(f"  NEW GATI-SETU ETA:   {stn['predicted_arrival_time']} (Dynamic Delay: +{stn['predicted_delay_min']}m)")
        print(f"  Confidence Interval: [{stn['confidence_bounds_p10_p90'][0]} P10 <-> {stn['confidence_bounds_p10_p90'][1]} P90]")
        print(f"  Old Formula Error:   +{stn['algorithm_correction_min']} min under-prediction")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    t_no = sys.argv[1] if len(sys.argv) > 1 else "12951"
    run_cli(t_no)

