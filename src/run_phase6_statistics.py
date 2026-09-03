"""Phase 6 paired forecast-error comparison for walk-forward predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm


REFERENCE = "compact_edge_linear_float32"
COMPARATORS = [
    "linear_regression",
    "random_forest",
    "hist_gradient_boosting",
    "seasonal_naive_lag_48",
    "persistence_lag_1",
]
DISPLAY_NAMES = {
    "linear_regression": "Linear regression",
    "random_forest": "Random forest",
    "hist_gradient_boosting": "Hist. gradient boost",
    "seasonal_naive_lag_48": "Seasonal naive (48)",
    "persistence_lag_1": "Persistence (1)",
}
SEED = 42
BOOTSTRAP_REPLICATES = 10_000
BLOCK_LENGTH = 48
HAC_LAG = 48


def moving_block_means(
    values: np.ndarray,
    replicates: int,
    block_length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Bootstrap the mean using sampled contiguous, non-circular blocks."""
    n = len(values)
    blocks_per_replicate = int(np.ceil(n / block_length))
    maximum_start = n - block_length
    output = np.empty(replicates, dtype=np.float64)
    batch_size = 250
    offsets = np.arange(block_length)
    for batch_start in range(0, replicates, batch_size):
        batch_end = min(batch_start + batch_size, replicates)
        starts = rng.integers(
            0,
            maximum_start + 1,
            size=(batch_end - batch_start, blocks_per_replicate),
        )
        indices = (starts[..., None] + offsets).reshape(batch_end - batch_start, -1)
        indices = indices[:, :n]
        output[batch_start:batch_end] = values[indices].mean(axis=1)
    return output


def hac_loss_test(values: np.ndarray, maximum_lag: int) -> dict[str, float]:
    """Two-sided HAC-normal test of whether the mean loss difference is zero."""
    n = len(values)
    mean = float(values.mean())
    centered = values - mean
    long_run_variance = float(np.dot(centered, centered) / n)
    for lag in range(1, maximum_lag + 1):
        weight = 1.0 - lag / (maximum_lag + 1.0)
        autocovariance = float(np.dot(centered[lag:], centered[:-lag]) / n)
        long_run_variance += 2.0 * weight * autocovariance
    long_run_variance = max(long_run_variance, 0.0)
    standard_error = np.sqrt(long_run_variance / n)
    if standard_error == 0.0:
        statistic = 0.0 if mean == 0.0 else np.sign(mean) * np.inf
        p_value = 1.0 if mean == 0.0 else 0.0
    else:
        statistic = mean / standard_error
        p_value = float(2.0 * norm.sf(abs(statistic)))
    return {
        "mean_loss_difference": mean,
        "hac_lag": maximum_lag,
        "long_run_variance": long_run_variance,
        "standard_error": float(standard_error),
        "z_statistic": float(statistic),
        "two_sided_p_value_unadjusted": p_value,
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(count, dtype=np.float64)
    running_maximum = 0.0
    for rank, original_index in enumerate(order):
        candidate = min(1.0, (count - rank) * p_values[original_index])
        running_maximum = max(running_maximum, candidate)
        adjusted[original_index] = running_maximum
    return adjusted.tolist()


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        type=Path,
        default=repository / "results/phase5_walk_forward_predictions.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=repository / "results"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prediction_path = args.predictions.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(prediction_path, parse_dates=["Timestamp"])
    if len(frame) != 2000 or frame["Timestamp"].duplicated().any():
        raise ValueError("Expected 2,000 unique walk-forward prediction timestamps")
    actual = frame["actual_normalized"].to_numpy(dtype=np.float64)
    reference_error = np.abs(actual - frame[REFERENCE].to_numpy(dtype=np.float64))

    results: list[dict[str, object]] = []
    for comparator_index, comparator in enumerate(COMPARATORS):
        comparator_error = np.abs(
            actual - frame[comparator].to_numpy(dtype=np.float64)
        )
        difference = reference_error - comparator_error
        rng = np.random.default_rng(SEED + comparator_index)
        bootstrap_means = moving_block_means(
            difference, BOOTSTRAP_REPLICATES, BLOCK_LENGTH, rng
        )
        ci_lower, ci_upper = np.quantile(bootstrap_means, [0.025, 0.975])
        comparator_mae = float(comparator_error.mean())
        result = {
            "reference": REFERENCE,
            "comparator": comparator,
            "paired_observations": len(difference),
            "reference_mae": float(reference_error.mean()),
            "comparator_mae": comparator_mae,
            "mae_difference_reference_minus_comparator": float(difference.mean()),
            "relative_mae_change_percent": float(
                100.0 * difference.mean() / comparator_mae
            ),
            "moving_block_bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "block_length": BLOCK_LENGTH,
                "ci95_lower": float(ci_lower),
                "ci95_upper": float(ci_upper),
                "ci_excludes_zero": bool(ci_lower > 0 or ci_upper < 0),
            },
            "paired_outcomes": {
                "reference_lower_absolute_error": int(np.sum(difference < 0)),
                "equal_absolute_error": int(np.sum(difference == 0)),
                "reference_higher_absolute_error": int(np.sum(difference > 0)),
            },
            "hac_absolute_loss_test": hac_loss_test(difference, HAC_LAG),
        }
        results.append(result)

    adjusted = holm_adjust(
        [
            float(row["hac_absolute_loss_test"]["two_sided_p_value_unadjusted"])
            for row in results
        ]
    )
    for row, adjusted_p in zip(results, adjusted):
        row["hac_absolute_loss_test"]["holm_adjusted_p_value"] = adjusted_p
        row["hac_absolute_loss_test"]["significant_at_0_05_after_holm"] = bool(
            adjusted_p < 0.05
        )
        mean_difference = float(row["mae_difference_reference_minus_comparator"])
        row["interpretation"] = (
            "negative favors compact edge model; positive favors comparator; "
            + (
                "paired difference is statistically distinguishable at alpha=0.05 "
                "under the stated HAC/Holm procedure"
                if adjusted_p < 0.05
                else "paired difference is not statistically distinguishable at alpha=0.05 "
                "under the stated HAC/Holm procedure"
            )
            + f"; observed direction={'compact' if mean_difference < 0 else 'comparator'}"
        )

    report = {
        "phase": 6,
        "experiment": "paired_forecast_error_comparison",
        "loss": "absolute error in normalized target units",
        "difference_definition": "absolute error of compact edge model minus comparator",
        "reference_model": REFERENCE,
        "observations": len(frame),
        "bootstrap": {
            "method": "moving-block percentile confidence interval",
            "replicates": BOOTSTRAP_REPLICATES,
            "block_length": BLOCK_LENGTH,
            "block_interpretation": "one day of half-hourly observations",
            "seed_base": SEED,
        },
        "loss_differential_test": {
            "method": "Diebold-Mariano-style mean loss-differential test with Bartlett Newey-West HAC variance",
            "hac_lag": HAC_LAG,
            "reference_distribution": "asymptotic standard normal",
            "multiple_comparison_adjustment": "Holm over five reference comparisons",
            "alpha": 0.05,
        },
        "comparisons": results,
        "limitations": [
            "The five model fits use expanding, overlapping training histories.",
            "Only 2,000 predictions from a short normalized case study are tested.",
            "Block length and HAC lag were fixed at one day rather than selected by an independent rule.",
            "The asymptotic HAC test is DM-style, not a guarantee that every classical DM assumption holds.",
            "Statistical significance does not establish practical importance or cross-dataset generalization.",
        ],
    }
    (output_dir / "phase6_statistical_comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    flat_rows = []
    for row in results:
        flat_rows.append(
            {
                "reference": row["reference"],
                "comparator": row["comparator"],
                "observations": row["paired_observations"],
                "reference_mae": row["reference_mae"],
                "comparator_mae": row["comparator_mae"],
                "mae_difference_reference_minus_comparator": row[
                    "mae_difference_reference_minus_comparator"
                ],
                "relative_mae_change_percent": row["relative_mae_change_percent"],
                "bootstrap_ci95_lower": row["moving_block_bootstrap"]["ci95_lower"],
                "bootstrap_ci95_upper": row["moving_block_bootstrap"]["ci95_upper"],
                "hac_z": row["hac_absolute_loss_test"]["z_statistic"],
                "hac_p_unadjusted": row["hac_absolute_loss_test"][
                    "two_sided_p_value_unadjusted"
                ],
                "holm_p": row["hac_absolute_loss_test"]["holm_adjusted_p_value"],
                "holm_significant_0_05": row["hac_absolute_loss_test"][
                    "significant_at_0_05_after_holm"
                ],
            }
        )
    pd.DataFrame(flat_rows).to_csv(
        output_dir / "phase6_statistical_comparison.csv", index=False
    )

    differences = [
        float(row["mae_difference_reference_minus_comparator"]) for row in results
    ]
    lower_errors = [
        difference - float(row["moving_block_bootstrap"]["ci95_lower"])
        for difference, row in zip(differences, results)
    ]
    upper_errors = [
        float(row["moving_block_bootstrap"]["ci95_upper"]) - difference
        for difference, row in zip(differences, results)
    ]
    positions = np.arange(len(results))
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    ax.errorbar(
        differences,
        positions,
        xerr=np.vstack([lower_errors, upper_errors]),
        fmt="o",
        color="#2878B5",
        ecolor="#333333",
        capsize=5,
    )
    ax.axvline(0.0, color="#C44E52", linestyle="--", linewidth=1.2)
    ax.set_yticks(positions, [DISPLAY_NAMES[row["comparator"]] for row in results])
    ax.set_xlabel("Paired MAE difference: compact edge minus comparator")
    ax.set_title("Phase 6: daily-block bootstrap intervals (negative favors compact)")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase6_paired_mae_differences.png", dpi=200)
    plt.close(fig)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
