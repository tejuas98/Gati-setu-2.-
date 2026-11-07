"""
Where Is My Train (WIMT) Reverse-Engineered Core Package
Enhanced with Train Physics, Adverse Weather Speed Restrictions & Dynamic ETA Prediction.
"""

from .train_physics import TrainPhysicsEngine, LocomotiveProfile
from .weather_engine import WeatherSafetyEngine, WeatherCondition
from .asset_database import WIMTAssetDatabase
from .cell_tower_engine import CellTowerTriangulator
from .dynamic_eta_service import WIMTDynamicETAService

__all__ = [
    "TrainPhysicsEngine",
    "LocomotiveProfile",
    "WeatherSafetyEngine",
    "WeatherCondition",
    "WIMTAssetDatabase",
    "CellTowerTriangulator",
    "WIMTDynamicETAService"
]

