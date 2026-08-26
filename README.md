# Smart-Meter Energy Load Forecasting

A reproducible machine-learning notebook for short-term electricity-load forecasting and anomaly investigation using smart-meter readings.

## Overview

The project uses a chronological train/test split to avoid time-series leakage. It engineers calendar and lag features, compares forecasting baselines, and evaluates two complementary anomaly-detection approaches:

- Forecast-residual thresholding from a Random Forest regressor
- Isolation Forest for unsupervised anomaly detection

The notebook is designed as a research-ready baseline that can later support ESP8266/ESP32-based sensing and alerting workflows.

## Dataset

The notebook uses the [Smart Meter Electricity Consumption Dataset](https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset) on Kaggle. The data is not included in this repository; obtain it from the original source and follow its terms of use.

## Results in the included run

- 5,000 smart-meter readings at 30-minute intervals
- Linear Regression: MAE 0.1310 kWh; RMSE 0.1625 kWh
- Random Forest: MAE 0.1328 kWh; RMSE 0.1652 kWh
- Forecast-residual detector: precision 0.900, recall 0.173, F1-score 0.290
- Isolation Forest detector: precision 0.250, recall 0.058, F1-score 0.094

These are baseline results using the dataset's provided labels, not validated field-deployment performance.

## Run locally

1. Create a Python 3.10+ environment.
2. Install requirements with pip install -r requirements.txt.
3. Download the dataset from Kaggle, update the data path if needed, and run the notebook from top to bottom.

See the [hosted Kaggle notebook](https://www.kaggle.com/code/fouadiqbal/smart-meter-energy-load-forecasting) for the verified run.

## Future directions

- Walk-forward validation
- Verified real-meter event evaluation
- Compact ESP32 edge-alert prototype

## License

MIT. The dataset remains subject to its original terms.
