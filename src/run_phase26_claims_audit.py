"""Audit public-facing project text for Phase 26 overclaiming risks."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "phase26_claims_audit.json"

TERMS = {
    "smart_meter": re.compile(r"\bsmart[- ]meter(?:ing|s)?\b", re.I),
    "real_time": re.compile(r"\breal[- ]time\b", re.I),
    "field_validated": re.compile(r"\bfield[- ]validated\b", re.I),
    "accurate_anomaly_detection": re.compile(r"\baccurate anomaly detection\b", re.I),
    "deployable": re.compile(r"\bdeployable\b", re.I),
    "energy_efficient": re.compile(r"\benergy[- ]efficient\b|\benergy efficiency\b", re.I),
    "low_power": re.compile(r"\blow[- ]power\b", re.I),
    "secure": re.compile(r"\bsecure(?:d|ly)?\b|\bsecurity\b", re.I),
    "real_world": re.compile(r"\breal[- ]world\b", re.I),
    "generalizable": re.compile(r"\bgeneraliz(?:able|ability|ation|e|ed)\b", re.I),
    "first": re.compile(r"\bfirst\b", re.I),
    "novel": re.compile(r"\bnovel(?:ty)?\b", re.I),
}

NEGATION_OR_BOUNDARY = re.compile(
    r"\b(?:not|no|without|prohibit|prevent|cannot|do not|does not|did not|"
    r"unverified|undocumented|future|reserved|prior art|claim boundary|limitation)\b",
    re.I,
)

SMART_METER_CONTEXT = re.compile(
    r"dataset|listing|style|workflow|prior art|future|reserved|calibrat|"
    r"not |no claim|does not|title|keyword|source",
    re.I,
)

SURFACES = [
    ROOT / "README.md",
    ROOT / "smart_meter_energy_load_forecasting.ipynb",
    ROOT / "firmware" / "esp8266_smart_meter" / "README.md",
    ROOT / "manuscript" / "smart_meter_esp8266_edge_ml.tex",
]

STALE_PATTERNS = {
    "obsolete_timing_mean_50_751": re.compile(r"50\.751"),
    "obsolete_three_by_16000_protocol": re.compile(r"three\s+16,?000", re.I),
    "unqualified_5000_smart_meter_readings": re.compile(r"5,000 smart[- ]meter readings", re.I),
    "numeric_kwh_result": re.compile(
        r"(?:MAE|RMSE|threshold|difference|error)[^\n.]{0,80}\d[^\n.]{0,30}\bkWh\b",
        re.I,
    ),
}


def notebook_records(path: Path) -> list[dict]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for index, cell in enumerate(notebook.get("cells", [])):
        text = "".join(cell.get("source", []))
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                records.append(
                    {
                        "location": f"cell {index}, source line {line_number}",
                        "text": line.strip(),
                    }
                )
    return records


def text_records(path: Path) -> list[dict]:
    return [
        {"location": f"line {number}", "text": line.strip()}
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip()
    ]


def classify(term: str, text: str) -> str:
    if term == "smart_meter" and SMART_METER_CONTEXT.search(text):
        return "contextual_or_explicit_boundary"
    if NEGATION_OR_BOUNDARY.search(text):
        return "explicitly_bounded"
    return "manual_review_required"


def main() -> None:
    occurrences = []
    stale = []
    source_summary = []
    traceback_cells = []

    for path in SURFACES:
        relative = path.relative_to(ROOT).as_posix()
        records = notebook_records(path) if path.suffix == ".ipynb" else text_records(path)
        source_summary.append({"path": relative, "nonblank_records": len(records)})
        all_text = "\n".join(record["text"] for record in records)

        if path.suffix == ".ipynb":
            notebook = json.loads(path.read_text(encoding="utf-8"))
            traceback_cells.extend(
                {
                    "path": relative,
                    "cell": index,
                }
                for index, cell in enumerate(notebook.get("cells", []))
                if cell.get("cell_type") == "code"
                and "".join(cell.get("source", [])).lstrip().startswith("Traceback (")
            )

        for record in records:
            for term, pattern in TERMS.items():
                if pattern.search(record["text"]):
                    occurrences.append(
                        {
                            "path": relative,
                            "location": record["location"],
                            "term": term,
                            "disposition": classify(term, record["text"]),
                            "context": record["text"][:1000],
                        }
                    )

        for name, pattern in STALE_PATTERNS.items():
            if pattern.search(all_text):
                stale.append({"path": relative, "pattern": name})

    manual_review = [item for item in occurrences if item["disposition"] == "manual_review_required"]
    # All manual-review items are retained in the evidence record. Phase 26 passes only
    # when the reviewed list below contains no assertion treated as a project claim.
    reviewed_nonclaims = []
    unsupported = []
    for item in manual_review:
        text = item["context"].lower()
        if item["term"] == "smart_meter" and any(
            token in text
            for token in (
                "smart-meter-style",
                "dataset",
                "listing",
                "workflow",
                "# smart-meter energy",
                "# esp8266 smart-meter prototype",
                "smart-meter ml project",
                "kaggle.com/code/",
            )
        ):
            reviewed_nonclaims.append({**item, "review": "descriptive dataset or workflow context"})
        elif item["term"] == "first" and any(
            token in text for token in ("first inspection", "first timestamp", "first ml model")
        ):
            reviewed_nonclaims.append({**item, "review": "ordinary sequence label, not a priority claim"})
        elif item["term"] == "secure" and any(
            token in text for token in ("migrate to", "before field deployment", "future")
        ):
            reviewed_nonclaims.append({**item, "review": "future security requirement, not a current capability claim"})
        elif item["term"] in {"first", "novel", "real_time"} and "\\cite" in item["context"]:
            reviewed_nonclaims.append({**item, "review": "description of cited prior work"})
        else:
            unsupported.append(item)

    report = {
        "phase": 26,
        "audit_date_local": "2026-09-03",
        "status": "passed" if not unsupported and not stale and not traceback_cells else "failed",
        "scope": source_summary,
        "candidate_occurrences": occurrences,
        "reviewed_contextual_nonclaims": reviewed_nonclaims,
        "unsupported_claims_remaining": unsupported,
        "stale_or_misleading_result_patterns": stale,
        "traceback_code_cells": traceback_cells,
        "approved_claim_boundary": (
            "The project demonstrates reproducible numerical and threshold-decision portability "
            "for a compact model under complete 933-vector replay on one physical ESP8266, with "
            "measured model-kernel timing and whole-firmware resource accounting."
        ),
        "claims_not_supported": [
            "calibrated smart-meter sensing or verified physical kWh",
            "independently validated real-event anomaly detection",
            "live on-device forecasting from a maintained lag buffer",
            "end-to-end or network latency from the kernel benchmark",
            "measured power or energy per inference",
            "secure field deployment",
            "cross-dataset or seasonal generalization",
            "algorithmic novelty or a worldwide first",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Phase 26 claims audit: {report['status'].upper()}")
    print(f"Candidate occurrences: {len(occurrences)}")
    print(f"Unsupported remaining: {len(unsupported)}; stale patterns: {len(stale)}")
    print(f"Traceback code cells: {len(traceback_cells)}")
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
