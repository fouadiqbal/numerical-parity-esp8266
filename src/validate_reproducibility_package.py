"""Validate the generated public reproducibility package without source data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "release" / "smart-meter-esp8266-reproducibility"
DENIED_NAMES = {
    "secrets.h",
    "tinyml_validation_data.h",
    "smart_meter_data.csv",
    "smart-meter-dataset.zip",
}
SECRET_PATTERNS = {
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    "assigned_secret": re.compile(
        r"(?i)(?:api[_ -]?key|password)\s*[=:]\s*[\"'][A-Za-z0-9_\-!@#$%^&*]{8,}[\"']"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate(package: Path) -> dict:
    manifest_path = package / "REPRODUCIBILITY_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {record["path"]: record for record in manifest["files"]}
    actual = {
        path.relative_to(package).as_posix(): path
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "REPRODUCIBILITY_MANIFEST.json"
        and ".git" not in path.relative_to(package).parts
    }

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        relative
        for relative in set(expected) & set(actual)
        if expected[relative]["bytes"] != actual[relative].stat().st_size
        or expected[relative]["sha256"] != sha256(actual[relative])
    )

    json_files = 0
    notebook_outputs = 0
    denied = []
    secret_counts = {name: 0 for name in SECRET_PATTERNS}
    absolute_workspace_paths = []
    unadapted_layout_paths = []
    checked_text_files = 0

    for relative, path in actual.items():
        if path.name in DENIED_NAMES:
            denied.append(relative)
        if path.suffix.lower() in {".json", ".ipynb"}:
            payload = json.loads(path.read_text(encoding="utf-8"))
            json_files += 1
            if path.suffix.lower() == ".ipynb":
                notebook_outputs += sum(
                    len(cell.get("outputs", [])) for cell in payload.get("cells", [])
                )
        if path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        checked_text_files += 1
        for name, pattern in SECRET_PATTERNS.items():
            secret_counts[name] += len(pattern.findall(text))
        executable_source = relative.startswith(("src/", "esp8266/", "tests/"))
        if executable_source and relative != "src/validate_reproducibility_package.py":
            private_windows_root = "C:" + "\\Users\\" + "fouad"
            if private_windows_root in text or "/C:/Users/fouad" in text:
                absolute_workspace_paths.append(relative)
            legacy_firmware_path = "firmware" + "/esp8266_smart_meter"
            if legacy_firmware_path in text or "ROOT / \"outputs\"" in text:
                unadapted_layout_paths.append(relative)

    passed = not any(
        (
            missing,
            extra,
            mismatched,
            denied,
            notebook_outputs,
            sum(secret_counts.values()),
            absolute_workspace_paths,
            unadapted_layout_paths,
        )
    )
    return {
        "status": "passed" if passed else "failed",
        "manifested_files": len(expected),
        "manifest_missing": missing,
        "manifest_extra": extra,
        "manifest_hash_or_size_mismatches": mismatched,
        "json_and_notebook_files_parsed": json_files,
        "text_files_scanned": checked_text_files,
        "stored_notebook_outputs": notebook_outputs,
        "denied_files": denied,
        "secret_pattern_matches_without_values": secret_counts,
        "absolute_workspace_paths": absolute_workspace_paths,
        "unadapted_layout_paths": unadapted_layout_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.package.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
