"""
Train Physics & Dynamics Engine for Where Is My Train
Implements locomotive tractive effort curves, Davis resistance equations,
trailing rake inertia, and service braking distances.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LocomotiveProfile:
    loco_type: str
    power_hp: int
    tractive_effort_kn: float
    max_tractive_effort_kn: float
    mps_kmh: float
    loco_mass_tons: float
    base_accel_m_s2: float


class TrainPhysicsEngine:
    # Calibrated Indian Railways locomotive registry
    LOCOMOTIVE_REGISTRY: Dict[str, LocomotiveProfile] = {
        "WAP7": LocomotiveProfile(
            loco_type="WAP-7 (Electric 3-Phase)",
            power_hp=6000,
            tractive_effort_kn=325.0,
            max_tractive_effort_kn=450.0,
            mps_kmh=130.0,
            loco_mass_tons=123.0,
            base_accel_m_s2=0.38
        ),
        "WAP4": LocomotiveProfile(
            loco_type="WAP-4 (Electric Conventional)",
            power_hp=5000,
            tractive_effort_kn=250.0,
            max_tractive_effort_kn=308.0,
            mps_kmh=110.0,
            loco_mass_tons=112.8,
            base_accel_m_s2=0.30
        ),
        "WDP4D": LocomotiveProfile(
            loco_type="WDP-4D (Dual Cab Diesel)",
            power_hp=4500,
            tractive_effort_kn=200.0,
            max_tractive_effort_kn=400.0,
            mps_kmh=120.0,
            loco_mass_tons=123.0,
            base_accel_m_s2=0.28
        ),
        "WDM3A": LocomotiveProfile(
            loco_type="WDM-3A (Alco Diesel)",
            power_hp=3100,
            tractive_effort_kn=180.0,
            max_tractive_effort_kn=305.0,
            mps_kmh=100.0,
            loco_mass_tons=112.5,
            base_accel_m_s2=0.22
        )
    }

    @classmethod
    def resolve_locomotive(cls, loco_serial: Optional[str]) -> LocomotiveProfile:
        """Resolves Indian Railways locomotive serial numbers into physical performance profiles."""
        s = str(loco_serial or "").strip()
        if s.startswith(("30", "37", "39", "27")):
            return cls.LOCOMOTIVE_REGISTRY["WAP7"]
        elif s.startswith(("21", "22")):
            return cls.LOCOMOTIVE_REGISTRY["WAP4"]
        elif s.startswith(("40", "41")):
            return cls.LOCOMOTIVE_REGISTRY["WDP4D"]
        elif s.startswith(("11", "12", "14", "16", "17", "18")):
            return cls.LOCOMOTIVE_REGISTRY["WDM3A"]
        return cls.LOCOMOTIVE_REGISTRY["WAP7"]

    @classmethod
    def calculate_dynamics(
        cls,
        loco: LocomotiveProfile,
        coach_count: int,
        speed_kmh: float,
        is_lhb: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates instantaneous train physics:
        1. Total train mass (loco + rake).
        2. Davis train resistance force (rolling, flange, aerodynamic).
        3. Net acceleration rate out of halts / speed restrictions.
        4. Service braking distance.
        """
        # LHB coach average tare = 42 tons + 6 tons payload; ICF average = 44 tons + 6 tons
        coach_tare = 48.0 if is_lhb else 50.0
        trailing_mass = coach_count * coach_tare
        total_mass_tons = loco.loco_mass_tons + trailing_mass

        # Davis Resistance Equation: R = A + B*v + C*v^2
        v_ms = speed_kmh / 3.6
        weight_kn = total_mass_tons * 9.81

        r_rolling = 0.0015 * weight_kn
        r_mechanical = 0.00012 * weight_kn * v_ms
        # LHB aerodynamic drag is 15% lower than blunt ICF rakes
        aero_coeff = 0.00032 if is_lhb else 0.00038
        r_aero = aero_coeff * 11.5 * (v_ms ** 2)
        total_resistance_kn = round((r_rolling + r_mechanical + r_aero) / 1000.0, 3)

        # Net Acceleration: (Tractive Effort - Resistance) / Mass
        net_force_kn = max(0.0, loco.tractive_effort_kn - total_resistance_kn)
        accel_m_s2 = round((net_force_kn * 1000.0) / (total_mass_tons * 1000.0), 3)

        # Service Braking Distance from current speed at standard -0.65 m/s^2
        b_service = 0.65
        brake_dist_m = round((v_ms ** 2) / (2.0 * b_service), 1) if v_ms > 0 else 0.0

        return {
            "locomotive_type": loco.loco_type,
            "power_hp": loco.power_hp,
            "continuous_tractive_effort_kn": loco.tractive_effort_kn,
            "locomotive_mass_tons": loco.loco_mass_tons,
            "coach_count": coach_count,
            "rake_type": "LHB Rake" if is_lhb else "ICF Rake",
            "trailing_rake_mass_tons": trailing_mass,
            "total_train_mass_tons": total_mass_tons,
            "davis_train_resistance_kn": total_resistance_kn,
            "net_acceleration_rate_m_s2": accel_m_s2,
            "service_braking_distance_m": brake_dist_m,
            "max_permissible_speed_kmh": loco.mps_kmh
        }

