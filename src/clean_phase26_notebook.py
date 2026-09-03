"""Apply Phase 26 scientific-label and corruption fixes to the teaching notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "smart_meter_energy_load_forecasting.ipynb"


REPLACEMENTS = (
    ("Electricity Consumed (kWh)", "Electricity Consumed (normalized units)"),
    ("MAE (kWh)", "MAE (normalized units)"),
    ("RMSE (kWh)", "RMSE (normalized units)"),
    ("{mae_baseline:.4f} kWh", "{mae_baseline:.4f} normalized target units"),
    ("{rmse_baseline:.4f} kWh", "{rmse_baseline:.4f} normalized target units"),
    ("{mae_linear:.4f} kWh", "{mae_linear:.4f} normalized target units"),
    ("{rmse_linear:.4f} kWh", "{rmse_linear:.4f} normalized target units"),
    ("{mae_rf:.4f} kWh", "{mae_rf:.4f} normalized target units"),
    ("{rmse_rf:.4f} kWh", "{rmse_rf:.4f} normalized target units"),
    ("{anomaly_threshold:.4f} kWh", "{anomaly_threshold:.4f} normalized target units"),
    ("0.1882 kWh", "0.1882 normalized target units"),
    ("0.2322 kWh", "0.2322 normalized target units"),
    ("0.3976 kWh", "0.3976 normalized target units"),
    ("Actual − Predicted (kWh)", "Actual − Predicted (normalized units)"),
    ("Absolute error (kWh)", "Absolute error (normalized units)"),
    ("Forecast (kWh)", "Forecast (normalized units)"),
    ("Absolute Error (kWh)", "Absolute Error (normalized units)"),
    (
        "This simulates how a deployed smart-meter system would forecast future load.",
        "This approximates chronological one-step-ahead evaluation; it is not evidence of a deployed or calibrated smart-meter system.",
    ),
    (
        "significantly outperforms the simple persistence baseline",
        "has lower MAE and RMSE than the persistence baseline on this one held-out partition",
    ),
    (
        "This indicates that these features provide valuable information for predicting electricity consumption.",
        "This indicates that these features are useful within this dataset and split; broader generalization was not tested in this notebook.",
    ),
)


SCOPE_NOTE = {
    "cell_type": "markdown",
    "metadata": {"tags": ["phase26-scope-note"]},
    "source": [
        "> **Scientific scope.** The downloaded numeric target is normalized approximately to 0-1 and the source does not provide an inverse transformation. All MAE/RMSE values below are therefore reported in normalized target units, not verified kWh. The supplied anomaly labels and measurement provenance were not independently validated.\n"
    ],
}


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = []
    removed_traceback_cells = 0
    replacement_count = 0

    for cell in notebook.get("cells", []):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and source.lstrip().startswith("Traceback ("):
            removed_traceback_cells += 1
            continue
        for old, new in REPLACEMENTS:
            occurrences = source.count(old)
            if occurrences:
                source = source.replace(old, new)
                replacement_count += occurrences
        cell["source"] = source.splitlines(keepends=True)
        cells.append(cell)

    if not any("phase26-scope-note" in cell.get("metadata", {}).get("tags", []) for cell in cells):
        insert_at = 2 if len(cells) >= 2 else len(cells)
        cells.insert(insert_at, SCOPE_NOTE)

    notebook["cells"] = cells
    NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {NOTEBOOK}")
    print(f"Text replacements: {replacement_count}; traceback code cells removed: {removed_traceback_cells}")


if __name__ == "__main__":
    main()
