# Building a UAP‑Forecast Engine  
*A practical blueprint for predicting future UFO / UAP sighting hotspots*  

---

## 1 Overview  
This guide distills a full workflow—data collection, cleaning, feature engineering, modeling, evaluation, and deployment—so you can prototype a “where‑and‑when” prediction service for unidentified aerial phenomena (UAP) reports.

---

## 2 Data Sources  

| Layer | Primary Datasets | Notes |
|-------|------------------|-------|
| **Core sightings** | **NUFORC master CSV** (≈ 80 k reports, 1910‑present)  | Open, downloadable; lat/long, timestamp, shape, duration, free‑text summary. |
| | **MUFON Case Management System (CMS)** | Pay‑walled; adds investigator disposition codes, weather/radar checks, detailed media. |
| **Environmental covariates** | • NASA VIIRS Cloud‑Cover Reanalysis  <br>• WorldPop population rasters  <br>• Global Human Footprint night‑light index  <br>• Airport / NOTAM shapefiles  | Improve signal‑to‑noise and correct for “more eyes → more reports.” |
| **Calendar & events** | Public‑holiday calendar, major launch schedules (SpaceX, ULA) | Captures holiday spikes and mis‑IDs from rocket launches. |

---

## 3 Data Cleaning & QA  

1. **Deduplicate** on `(event_date, city, summary_text)`.  
2. **Fix coordinates** – swap long/lat when absolute value > 90°.  
3. **Timestamp hygiene** – standardize `YYYY‑MM‑DD HH:MM` in UTC; flag unknown time as `12:00`.  
4. **Outlier removal** – drop duration > 24 h unless corroborated by CMS notes.  

A quick Pandas script usually cuts ~10–15 % bad rows from NUFORC.

---

## 4 Feature Engineering  

| Block | Implementation | Rationale |
|-------|---------------|-----------|
| **Spatiotemporal tiles** | Convert lat/long → 6‑char geohash; bucket time into 6‑hour slices. | Treats sightings like events in a crime‑prediction map. |
| **Population & tourism** | WorldPop + annual tourist nights per geohash. | More observers ⇒ higher report probability. |
| **Viewability** | Mean cloud‑cover & sky‑view factor per tile‑hour. | A spectacular craft goes unreported under heavy overcast. |
| **Air‑traffic proximity** | Distance to nearest airport, military range, starlink corridor. | Helps filter obvious conventional objects. |
| **Seasonality** | Month, weekday, holiday flag. | NUFORC shows > 40 % lift around holiday weekends. |

---

## 5 Modeling Approaches  

### 5.1 Quick Prototype  
**Spatio‑Temporal Kernel Density Estimation (STKDE)**  
```python
from skspatial_stats import stkde
heat = stkde.fit(events, bandwidth_space=0.3°, bandwidth_time=24h)
```
*Pros*: two parameters, instant heat‑maps.  
*Cons*: no covariates, limited forecasting horizon.

### 5.2 Machine‑Learning Stack  
1. **Gradient‑Boosted Decision Trees** (e.g., LightGBM) on engineered features – fast & interpretable.  
2. **ConvLSTM or ST‑GNN** when you have GPU budget and want the network to learn spatial filters automatically.  

---

## 6 Evaluation Metrics  

| Use‑case | Metric | Good Threshold |
|----------|--------|----------------|
| Sensor‑van patrol planning | **Predictive Accuracy Index (PAI)** | PAI ≥ 2 at 10 % area ⇒ double the hit‑rate over random deployment. |
| Tile‑level alerts | **Area‑Under Precision‑Recall (AUPRC)** | ≥ 0.20 on 10 km / 6‑h tiles is respectable given the rarity. |

Hold out the entire last year (e.g., train 2010‑2023, test 2024) to avoid leakage.

---

## 7 Serving the Forecasts  

1. **Nightly pipeline** (Python or Rust)  
   * Pull latest NUFORC CSV (or scrape CMS export).  
   * Clean & enrich with NOAA weather API.  
2. **Update model coefficients** or append new rows for incremental GBDT.  
3. **Publish vector tiles / GeoJSON** to S3 or CloudFront.  
4. **Front‑end**: React + Mapbox GL; burnt‑orange gradient for “BlockSignal”‑style hotspots.

**Cost**: AWS `t4g.medium` + Spot GPU ≈ \$40 / month for continental‑US at 10 km × 6 h resolution.

---

## 8 Legal & Ethical Caveats  

| Issue | Action |
|-------|--------|
| **MUFON redistribution ban** | Only publish aggregated stats & anonymized tiles. |
| **Witness PII** | Strip names, addresses, phone numbers in free‑text. |
| **Observer bias** | Clearly state forecasts predict *reports*, not underlying phenomena frequency. |

---

## 9 Accessing MUFON CMS  

| Level | Requirements | Privileges |
|-------|--------------|------------|
| **Basic visitor** | None (public site) | View 20 most‑recent cases, map pins, low‑res media. |
| **Enhanced member** | \$79 / yr | Full‑text search, medium‑res media, PDF export case‑by‑case. |
| **Field investigator** | Background check + training | Investigator portal at `mufoncms.com`; batch upload, high‑res evidence, disposition codes. |

There is **no official REST API**. Bulk access requires a Memorandum of Understanding (MoU) with MUFON HQ.

---

## 10 Next Steps Checklist  

```text
[ ] Download NUFORC CSV and run QA script  
[ ] Build STKDE heat‑map to sanity‑check spatial distribution  
[ ] Engineer covariates (population, cloud cover, holidays)  
[ ] Train LightGBM on 2010‑2023; evaluate on 2024 hold‑out  
[ ] Sign up for MUFON Enhanced membership for richer validation set  
[ ] Deploy nightly ETL → model → vector tiles → React dashboard  
```

---

*Happy hunting — may your hotspots be anomalous!*  
