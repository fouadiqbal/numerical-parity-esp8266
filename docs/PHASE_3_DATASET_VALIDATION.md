# Phase 3 — Dataset Provenance, License, and Suitability Audit

Status: **complete for the currently available evidence**  
Audit date: 2026-09-03  
Working file: `data/source/extracted/smart_meter_data.csv`

## Executive decision

The current Kaggle dataset may remain in the project as a **development and ESP8266 numerical-portability case study**, but it should **not remain the sole or primary scientific dataset for a conference submission**.

The main reasons are:

1. The Kaggle listing identifies the uploader but does not document an original measurement campaign, household/site, meter, collection hardware, geographic source, raw source, or preprocessing/inverse-scaling procedure.
2. Every continuous column in the downloaded file is bounded approximately from 0 to 1, although the page describes physical units such as kWh, degrees Celsius, percent humidity, and km/h.
3. The page states that anomaly labels were produced by Isolation Forest, so they are algorithm-generated labels rather than independent physical ground truth.
4. The file contains exactly 250 abnormal rows out of 5,000 (5%), but the Isolation Forest features, parameters, seed, contamination setting, training scope, and labeling code are not supplied.
5. The 104-day interval is too short to establish annual seasonal generalization.

The numerical ESP8266 parity result remains valid because parity concerns reproduction of the stored computation. However, its numerical unit must be reported as **normalized dataset target units**, not verified kWh.

## Dataset provenance table

| Item | Finding | Research status |
|---|---|---|
| Listing | [Smart Meter Electricity Consumption Dataset on Kaggle](https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset) | Verified listing |
| Kaggle publisher | Account `ziya07`, displayed as “Ziya” | Verified uploader identity only |
| Original data creator | Not identified separately from the uploader | Unverified |
| Version observed | Version 1; one CSV file | Verified from listing |
| License displayed | CC0: Public Domain | Verified on listing |
| Original collection provenance | No primary source, location, household/site, meter, or collection protocol documented | Missing |
| Sampling | Consecutive 30-minute timestamps | Verified locally |
| Local date range | 2024-01-01 00:00 to 2024-04-14 03:30 | Verified locally |
| Rows and columns | 5,000 rows, 7 columns | Verified locally |
| Missing/duplicate timestamps | 0 blank cells, 0 duplicate timestamps, 0 non-30-minute consecutive intervals | Verified locally |
| Continuous-value scale | All five numeric columns range from 0 to approximately 1 | Verified locally |
| Physical-unit mapping | No inverse-scaling metadata found | Missing |
| Label method | Listing says Isolation Forest | Publisher statement |
| Label distribution | Normal 4,750; Abnormal 250 | Verified locally |
| Label ground truth | No independent physical/event annotation documented | Unverified |
| Redistribution | Listing applies CC0, but upstream ownership/provenance is not documented | Legally permissive listing; provenance risk remains |

## Local integrity record

The reproducible script `tools/audit_dataset.py` generated `outputs/dataset_integrity.json`.

| Artifact | SHA-256 |
|---|---|
| `smart_meter_data.csv` | `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588` |
| `smart-meter-dataset.zip` | `A99DD2C759DD0A28EC3E68DEC22F3BF686266346473D1CFABAFD2679D042271F` |

Local acquisition timestamp from filesystem metadata: 2026-09-02. This timestamp records the local copy, not the Kaggle publication date.

## Unit-consistency finding

The source page describes:

- electricity consumption in kWh;
- temperature in degrees Celsius;
- humidity in percent;
- wind speed in km/h;
- average past consumption in kWh.

The downloaded file instead contains every numeric field on an approximately 0–1 scale. Without raw values, scaler minima/maxima, or an inverse transformation, the physical units cannot be reconstructed.

Consequences:

- Existing MAE and RMSE values must be labeled **normalized target units**.
- The maximum Python/device numerical difference must be labeled **normalized target units**.
- The manuscript’s kWh labels for these results require correction.
- Weather-effect interpretation in physical units is not currently defensible.
- Device parity remains a valid arithmetic result because both references use the same normalized inputs and target representation.

Legacy JSON keys ending in `_kwh` remain in existing evidence files for traceability, but they are not proof of physical units. They should be migrated carefully in a later reproducibility phase without losing the original evidence.

## Anomaly-label assessment

The Kaggle page states that labels were detected using Isolation Forest. This means the label column is an output of another algorithm, not an independently observed fault record. The page does not identify:

- input features used to create labels;
- training interval;
- Isolation Forest contamination setting;
- number of estimators or random seed;
- whether the full time series, including future rows, was used;
- whether labels were inspected by a domain expert;
- whether any physical electrical event occurred.

The exactly 5% abnormal fraction is consistent with a fixed contamination setting, but that is an inference, not a verified parameter.

Therefore the paper may say:

> “agreement with dataset-supplied, Isolation-Forest-generated labels.”

It must not say:

> “validated detection of real electrical anomalies.”

## License and publication assessment

The Kaggle listing displays a CC0 Public Domain license, which is permissive for reuse and derivatives. That makes analysis and publication of derived results practical. However, a displayed license does not resolve missing upstream provenance or prove that the uploader collected the observations or owned every source right.

Recommended publication practice:

1. Cite the exact Kaggle page, uploader name/account, version, access date, and local SHA-256.
2. Do not describe the file as measured household data unless a primary collection source is located.
3. Do not describe its normalized values as raw physical measurements.
4. Do not redistribute the raw CSV or full dataset-derived validation header in the public repository until the project’s final licensing audit reconfirms the scope.
5. Preserve the current data only as a reproducibility input obtained from the original listing.

## Stronger dataset recommendations

### 1. UCI Individual Household Electric Power Consumption — preferred forecasting dataset

Official source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual%2Bhousehold%2Belectric%2Bpower-consumption)  
DOI: [10.24432/C58K54](https://doi.org/10.24432/C58K54)  
License: CC BY 4.0

| Property | Value |
|---|---|
| Creators | Georges Hebrail and Alice Berard |
| Provenance | One household in Sceaux, France |
| Coverage | December 2006 to November 2010; approximately 47 months |
| Sampling | One minute |
| Size | 2,075,259 measurements; 9 variables |
| Physical measurements | Active power, reactive power, voltage, current, and three energy sub-meterings |
| Missingness | Approximately 1.25% of measurement rows contain missing values; timestamps remain present |
| Edge suitability | Aggregate or resample to 30 minutes, create causal lag/calendar features, and export a compact model |

Why it is stronger:

- Official academic repository, named creators, DOI, explicit license, long temporal coverage, physical units, and documented missingness.
- Four years permit meaningful seasonal-naive lag-48 evaluation and rolling-origin folds.
- It is a stronger primary dataset for forecasting, although it still represents only one household and contains no verified anomaly labels.

### 2. REFIT Electrical Load Measurements — preferred measured multi-household dataset

Official source: [University of Strathclyde research repository](https://pureportal.strath.ac.uk/en/datasets/refit-electrical-load-measurements/)  
Raw DOI: [10.15129/31da3ece-f902-4e95-a093-e0a9536983c4](https://doi.org/10.15129/31da3ece-f902-4e95-a093-e0a9536983c4)  
Cleaned DOI: [10.15129/9ab14b0e-19ac-4279-938f-27f643078cec](https://doi.org/10.15129/9ab14b0e-19ac-4279-938f-27f643078cec)  
License: CC BY 4.0

| Property | Value |
|---|---|
| Creators | David Murray, Lina Stankovic, and Vladimir Stankovic |
| Provenance | REFIT project; 20 UK households |
| Coverage | October 2013 to June 2015 |
| Sampling | Approximately 8 seconds |
| Measurements | Whole-house aggregate and appliance-level power in watts |
| Documentation | Collection and cleaning described in a peer-reviewed Scientific Data article |
| Edge suitability | Downsample or derive causal window features; suitable for forecasting, NILM, or compact event analysis |

Why it is stronger:

- It provides measured, multi-household data with named researchers, research funding context, DOI, CC BY license, and peer-reviewed technical validation.
- It offers a realistic path from model development to future sensor-oriented embedded work.
- Its larger size requires deliberate preprocessing and a documented household selection policy.

### 3. Annotated Load Anomalies from REFIT — preferred anomaly benchmark

Official source: [University of Strathclyde research repository](https://pureportal.strath.ac.uk/en/datasets/annotated-load-anomalies-from-the-refit-dataset/)  
DOI: [10.15129/9729a2a0-11ce-4cce-b0d0-144c483fcb33](https://doi.org/10.15129/9729a2a0-11ce-4cce-b0d0-144c483fcb33)  
License: CC BY 4.0

| Property | Value |
|---|---|
| Creators | Haroon Rashid, Vladimir Stankovic, Lina Stankovic, and Pushpendra Singh |
| Source | Derived from five REFIT houses with documented appliance-load anomalies |
| Coverage | Within the October 2013 to June 2015 REFIT period |
| Annotation | Rules are described in the accompanying peer-reviewed ICASSP 2019 paper |
| Scope | Appliance-level anomalies for refrigerators/freezers, dishwasher, washing machine, dryer, heater, and microwave |
| Edge suitability | Suitable for honest anomaly benchmarking and later compact-device decision reproduction |

Why it is stronger:

- It has a DOI, explicit CC BY 4.0 license, named academic creators, a linked peer-reviewed method, and documented anomaly semantics.
- It is much better suited to anomaly claims than labels generated by an undocumented Isolation Forest run.

## Dataset selection for subsequent phases

Recommended hierarchy:

1. **UCI household power consumption:** primary forecasting and walk-forward dataset after resampling to 30-minute energy/load intervals with a documented conversion.
2. **REFIT or annotated REFIT:** external measured-data and anomaly-analysis dataset, chosen according to experiment scope.
3. **Current Kaggle file:** retained as the original development/HIL parity case study, reported only in normalized units and never treated as calibrated field data.

Phase 4 should first preserve and reproduce the current-case baselines, then build a separate official-dataset pipeline rather than mixing two datasets into one split. The original 933-row HIL result must remain associated only with the current Kaggle-derived normalized dataset.

## Phase 3 conclusion

Publication and derivative analysis appear permitted under the CC0 designation displayed by Kaggle, but the dataset’s scientific provenance and physical units are inadequate for it to serve as the paper’s only primary dataset. The paper should add an official, DOI-backed measured dataset and correct all current unit labels. The anomaly study should use the annotated REFIT resource or restrict conclusions to agreement with algorithm-generated labels.
