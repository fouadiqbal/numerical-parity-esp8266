# Conference submission

The authoritative public paper is `smart_meter_esp8266_edge_ml.pdf`. It is the
six-page conference version submitted by the author, titled **Numerical-Parity
Transfer of a Compact Load-Forecasting and Residual-Decision Model to
ESP8266**.

The PDF is self-contained: all six paper figures are embedded. The same figures
are also retained in `../figures/` for review and reproducibility.

`smart_meter_esp8266_edge_ml_repository_source.tex` is the earlier repository
implementation source used to generate the experiments. It is retained for
auditability but is not presented as the exact camera-ready LaTeX source of the
submitted PDF. This distinction prevents a reviewer from mistaking the
repository source snapshot for the conference-layout source.

The paper reports normalized target units because the source dataset does not
provide inverse-scaling metadata. The ESP32 field-validation extension remains
explicitly reserved until calibrated hardware experiments exist.
