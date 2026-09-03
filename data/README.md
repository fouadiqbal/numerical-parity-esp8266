# Data acquisition and integrity

No raw dataset is distributed in this repository.

1. Visit the [Kaggle source listing](https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset).
2. Confirm the listing still shows **Version 1** and **CC0: Public Domain**.
3. Download `smart_meter_data.csv`, or use the Kaggle API:

   ```bash
   kaggle datasets download -d ziya07/smart-meter-electricity-consumption-dataset -p data/source --unzip
   ```

4. Place the CSV at `data/source/extracted/smart_meter_data.csv`.
5. Run `python src/audit_dataset.py` and verify this CSV SHA-256:

   `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588`

The recorded Kaggle archive SHA-256 is `A99DD2C759DD0A28EC3E68DEC22F3BF686266346473D1CFABAFD2679D042271F`, but API packaging can change while the extracted CSV remains identical.

The file has 5,000 rows and seven columns. Its continuous columns are normalized to approximately 0-1, and no inverse-scaling metadata is supplied. Report errors only in **normalized target units**, never verified kWh.

`split_indices.json` records deterministic half-open row ranges after chronological sorting and removal of the first 336 lag-incomplete rows. The anomaly labels are publisher-described Isolation Forest outputs, not independently verified electrical events.
