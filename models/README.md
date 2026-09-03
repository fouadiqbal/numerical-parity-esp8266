# Model artifacts

`model_manifest.json` records the exact feature order, split timestamps, float64 fitted parameters, serialized float32 parameters, decision threshold, environment, and model fingerprint.

Arduino requires local headers beside the sketch, so the executable generated models are stored in `../esp8266/`:

- `tinyml_model.h`: standardized FP32 reference model with eight compact regression vectors;
- `tinyml_fused_model.h`: algebraically fused FP32 form;
- `tinyml_fixed_model.h`: Q15/Q30 experimental form.

The complete 933-row `tinyml_validation_data.h` is deliberately absent. Regenerate it locally with `python src/train_tinyml_edge_model.py` after acquiring the source CSV. Do not commit it.
