# Indian Railways Live Telemetry: Google WIMT vs. GatiSetu Benchmark

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github&logoColor=white)](https://github.com/tejuas98/Gati-setu-2.-)
[![Kaggle Benchmark EDA](https://img.shields.io/badge/Kaggle-EDA_Notebook-20BEFF?style=flat&logo=kaggle&logoColor=white)](https://www.kaggle.com/code/rudraa11/gatisetu-telemetry-benchmark-eda)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg?style=flat)](https://creativecommons.org/publicdomain/zero/1.0/)

A nationwide empirical dataset benchmarking the **Official Where Is My Train / Google Static Algorithm** against the **GatiSetu Dynamic Physics & Weather Engine** across all 13,550 passenger services on Indian Railways.

Developed for **Smart India Hackathon (SIH 2026)** - Ministry of Railways - Problem Statement 26028.

---

## 1. Background & Problem Statement

Commercial train tracking applications (e.g. Where Is My Train / Google) compute future arrival times using a naive linear extrapolation formula:

```text
ETA_static = Scheduled Arrival (STA) + Current Cumulative Delay
```

This static formula assumes future track segments will be traversed under ideal conditions, ignoring:
1. **Adverse Weather:** Dense winter fog (< 100 m visibility) legally enforces a maximum speed of 60 km/h under Indian Railways FogPASS operating rules. Heavy monsoon rainfall (> 0.2 mm/h) and coastal winds reduce steel rail adhesion, requiring extended braking distances.
2. **Junction Turnout Queuing:** Interlocking bottlenecks at major railway junctions (e.g., Pt. Deen Dayal Upadhyaya Jn [DDU], Kanpur Central [CNB], Bhusaval [BSL], Itarsi [ET]).

The **GatiSetu AI Engine** combines live locomotive telemetry, Davis train resistance physics, and real-time micro-weather telemetry from Open-Meteo to compute dynamic arrival forecasts:

```text
ETA_gatisetu = STA + Current Delay + Δt(weather_cap) + Δt(junction_bottleneck) + Δt(adhesion_braking)
```

---

## 2. Master Files in this Dataset

1. **`national_13550_train_telemetry_comparison_master.csv`** (2.8 MB, 13,550 rows):
   - Comprehensive side-by-side comparison for **every single train** in Indian Railways.
   - For every train, shows: Scheduled STA, Static Google ETA, GatiSetu Physics ETA, divergence delta in minutes, live locomotive GPS speed, weather metrics, and operational root-cause tags.
   - Covers 100% of the passenger fleet: 3,235 trains with live ground-truth telemetry observations and 10,315 trains with scheduled fleet physics profiles.

2. **`official_24hr_national_benchmark.csv`** (1.7 MB, 8,176 rows):
   - Multi-cycle longitudinal ground-truth telemetry collected across 18 continuous nationwide sweeps.
   - Includes real-time locomotive GPS speed, next halt ETAs, destination ETAs, Open-Meteo weather parameters, and automated root-cause classifications.

3. **`all_13550_fleet_master.csv`** (2.5 MB, 13,550 rows):
   - Master passenger fleet catalog detailing train categories, speed tiers, sectional MPS limits, base cities, coach compositions, and GatiSetu physics model assignments.

---

## 3. Dataset Provenance and Collection Methodology

- **Locomotive Telemetry Source:** Indian Railways National Train Enquiry System (NTES) unauthenticated application gateway.
- **Weather Telemetry Source:** Open-Meteo High-Resolution Atmospheric Weather API (sampling localized visibility, precipitation, and wind gusts at locomotive coordinate blocks).
- **Fleet Schedule Database:** Where Is My Train offline SQLite railway network topology (13,550 trains, 10,083 stations).
- **Sampling Frequency:** Automated multi-cycle nationwide sweeps every ~15 minutes running on an asynchronous multi-threaded pipeline.
- **Source Code & Engine Repository:** [https://github.com/tejuas98/Gati-setu-2.-](https://github.com/tejuas98/Gati-setu-2.-)
