# Indian Railways Live Telemetry: Google WIMT vs. GatiSetu Benchmark

A real-world empirical dataset benchmarking the **Official Where Is My Train / Google Static Algorithm** against the **GatiSetu Dynamic Physics & Weather Engine** across active passenger trains on Indian Railways.

Developed for **Smart India Hackathon (SIH 2026)** - Problem Statement 26028.

---

## 1. Background & Problem Statement

Commercial train tracking applications (e.g. Where Is My Train / Google) compute future arrival times using a naive linear extrapolation formula:

$$\text{ETA}_{\text{static}} = \text{Scheduled Arrival (STA)} + \text{Current Cumulative Delay}$$

This static formula assumes future track segments will be traversed under ideal conditions, ignoring:
1. **Adverse Weather:** Dense winter fog ($< 100\text{ m}$ visibility) legally enforces a maximum speed of $60\text{ km/h}$ under Indian Railways FogPASS operating rules. Heavy monsoon rainfall ($> 0.2\text{ mm/h}$) and coastal winds reduce steel rail adhesion, requiring extended braking distances.
2. **Junction Turnout Queuing:** Interlocking bottlenecks at major railway junctions (e.g., Pt. Deen Dayal Upadhyaya Jn [DDU], Kanpur Central [CNB], Bhusaval [BSL], Itarsi [ET]).

The **GatiSetu AI Engine** combines live locomotive telemetry, Davis train resistance physics, and real-time micro-weather telemetry from Open-Meteo to compute dynamic arrival forecasts:

$$\text{ETA}_{\text{gatisetu}} = \text{STA} + \text{Current Delay} + \Delta t_{\text{weather\_cap}} + \Delta t_{\text{junction\_bottleneck}} + \Delta t_{\text{adhesion\_braking}}$$

---

## 2. Files in this Dataset

- **`national_train_telemetry_benchmark.csv`**: Multi-cycle nationwide train observations across active routes, comparing both Next Halt and Destination Terminus ETAs alongside live Open-Meteo weather parameters.
- **`priority_corridor_comparison_benchmark.csv`**: Targeted side-by-side evaluations across priority trunk trains (Rajdhanis, Superfast Expresses).

---

## 3. Data Dictionary

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `record_timestamp` | String | Timestamp of observation (`YYYY-MM-DD HH:MM:SS`) |
| `sweep_cycle` | Integer | Iteration cycle of the nationwide fleet sweep |
| `journey_start_date` | String | Official date of train departure (`YYYY-MM-DD`) |
| `train_no` | String | 5-digit Indian Railways train number |
| `train_name` | String | Official train service name |
| `train_type` | String | Train category (`SUF`=Superfast, `MEX`=Mail/Exp, `RAJ`=Rajdhani, `GBR`=Garib Rath) |
| `current_station_code` | String | Station code of the current block section location |
| `current_station_name` | String | Name of the current station |
| `current_delay_min` | Integer | Real-time cumulative delay in minutes |
| `speed_kmh` | Float | Real-time locomotive speed in km/h |
| `weather_condition` | String | Weather classification from Open-Meteo API |
| `visibility_km` | Float | Atmospheric horizontal visibility in km |
| `precipitation_mm` | Float | Real-time rainfall rate in mm/h |
| `wind_gusts_kmh` | Float | Peak wind gust speed in km/h |
| `speed_cap_kmh` | Float | Legally mandated maximum speed limit under local weather conditions |
| `is_weather_restricted`| Boolean | True if weather enforces a speed reduction below track MPS |
| `next_halt_name` | String | Immediate upcoming commercial halt name |
| `next_halt_code` | String | Immediate upcoming commercial halt code |
| `next_halt_sta` | String | Official scheduled arrival time at next halt (`HH:MM`) |
| `next_halt_google_eta` | String | Where Is My Train / Google static arrival prediction (`HH:MM`) |
| `next_halt_gatisetu_eta`| String | GatiSetu dynamic physics & weather arrival prediction (`HH:MM`) |
| `next_halt_delta_min` | Float | Formula divergence at next halt in minutes |
| `destination_name` | String | Final trip terminus name |
| `destination_code` | String | Final trip terminus code |
| `destination_sta` | String | Official scheduled arrival time at terminus (`HH:MM`) |
| `destination_google_eta`| String | Where Is My Train / Google static terminus prediction (`HH:MM`) |
| `destination_gatisetu_eta`| String | GatiSetu dynamic physics & weather terminus prediction (`HH:MM`) |
| `destination_delta_min`| Float | Cumulative formula divergence at trip terminus in minutes |
| `operational_cause_tag` | String | Root-cause tag (Weather Cap, Junction Bottleneck, Cumulative Congestion, Normal Running) |

---

## 4. Source & Citation

- **Telemetry Source:** Indian Railways National Train Enquiry System (NTES) / RailRadar live feed.
- **Weather Source:** Open-Meteo High-Resolution Weather API.
- **Project Repository:** [https://github.com/tejuas98/Gati-setu-2.-](https://github.com/tejuas98/Gati-setu-2.-)
