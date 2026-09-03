# LaTeX manuscript

Main source: `smart_meter_esp8266_edge_ml.tex`

Compile from this directory so that the relative figure and bibliography paths resolve:

```bash
pdflatex smart_meter_esp8266_edge_ml.tex
bibtex smart_meter_esp8266_edge_ml
pdflatex smart_meter_esp8266_edge_ml.tex
pdflatex smart_meter_esp8266_edge_ml.tex
```

The paper reports normalized target units because the source dataset does not provide an inverse transformation. The ESP32 field-validation section is intentionally reserved until calibrated hardware experiments exist.
