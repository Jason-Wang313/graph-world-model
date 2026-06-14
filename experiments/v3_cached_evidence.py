from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
OUT = RESULTS / "v3_cached_evidence"
OUT_FIGS = OUT / "figures"
PUB_FIGS = RESULTS / "figures" / "v3"
PAPER_DIR = ROOT / "paper" / "iclr"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        out = float(value)
        if math.isnan(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def inum(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(
        path,
        metadata={"Creator": "graph-world-model-v3-cache", "CreationDate": None, "ModDate": None},
    )
    plt.close()


def copy_public_figures() -> None:
    PUB_FIGS.mkdir(parents=True, exist_ok=True)
    for src in sorted(OUT_FIGS.glob("*.pdf")):
        (PUB_FIGS / src.name).write_bytes(src.read_bytes())


def artifact_inventory() -> tuple[list[dict[str, object]], Counter]:
    excluded_parts = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "build",
        "v3_cached_evidence",
        "final",
    }
    rows: list[dict[str, object]] = []
    counts: Counter = Counter()
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = set(rel.parts)
        if parts & excluded_parts:
            continue
        if rel.parts[:3] == ("results", "figures", "v3"):
            continue
        suffix = path.suffix.lower()
        if rel.parts[:2] == ("results", "tables"):
            category = "result_table"
        elif rel.parts[0] == "figures":
            category = "figure"
        elif rel.parts[0] == "src":
            category = "source"
        elif rel.parts[0] == "tests":
            category = "test"
        elif rel.parts[0] == "docs":
            category = "doc"
        elif rel.parts[0] == "scripts":
            category = "script"
        elif rel.parts[0] == "paper":
            category = "paper"
        elif suffix == ".json":
            category = "json"
        else:
            category = "other"
        counts[category] += 1
        rows.append(
            {
                "path": rel.as_posix(),
                "category": category,
                "bytes": path.stat().st_size,
            }
        )
    return rows, counts


def statistical_lookup(rows: list[dict[str, str]], scope: str, treatment: str, metric: str) -> dict[str, str]:
    for row in rows:
        if row.get("scope") == scope and row.get("treatment") == treatment and row.get("metric") == metric:
            return row
    raise KeyError((scope, treatment, metric))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)

    run_summary = read_json(RESULTS / "run_summary.json")
    claims_status = read_json(RESULTS / "claims_status.json")
    claim_map = read_json(RESULTS / "claim_evidence_map.json")
    main_rows = read_csv(TABLES / "main_metrics.csv")
    stress_rows = read_csv(TABLES / "stress_metrics.csv")
    stat_rows = read_csv(TABLES / "statistical_tests.csv")
    learned_rows = read_csv(TABLES / "learned_model_metrics.csv")
    exact_rows = read_csv(TABLES / "exact_law_validation.csv")

    claims = claims_status["claims"]
    supported_claims = [c for c in claims if c["status"] == "supported"]
    unsupported_claims = [c for c in claims if c["status"] == "unsupported"]
    claim_rows = [
        {
            "id": c["id"],
            "status": c["status"],
            "claim": c["claim"],
            "evidence": c.get("evidence", ""),
        }
        for c in claims
    ]
    write_csv(OUT / "v3_claim_inventory.csv", claim_rows, ["id", "status", "claim", "evidence"])

    raw64_stress = [r for r in stress_rows if r.get("selector") == "raw" and inum(r.get("N")) == 64]
    families = sorted({r["graph_family"] for r in raw64_stress})
    failures = sorted({r["hidden_failure"] for r in raw64_stress})
    matrix_rows: list[dict[str, object]] = []
    matrix = []
    for family in families:
        values = []
        for failure in failures:
            vals = [
                fnum(r["oracle_regret"])
                for r in raw64_stress
                if r["graph_family"] == family and r["hidden_failure"] == failure
            ]
            cell = mean(vals) if vals else 0.0
            values.append(cell)
            matrix_rows.append(
                {
                    "graph_family": family,
                    "hidden_failure": failure,
                    "mean_raw_n64_oracle_regret": cell,
                    "n_rows": len(vals),
                }
            )
        matrix.append(values)
    write_csv(
        OUT / "v3_constraint_shadow_matrix.csv",
        matrix_rows,
        ["graph_family", "hidden_failure", "mean_raw_n64_oracle_regret", "n_rows"],
    )

    family_rows: list[dict[str, object]] = []
    for family in families:
        raw_vals = [fnum(r["oracle_regret"]) for r in raw64_stress if r["graph_family"] == family]
        hidden_vals = [fnum(r["selected_hidden_energy"]) for r in raw64_stress if r["graph_family"] == family]
        util_vals = [fnum(r["selected_real_utility"]) for r in raw64_stress if r["graph_family"] == family]
        family_rows.append(
            {
                "graph_family": family,
                "raw_n64_oracle_regret": mean(raw_vals),
                "raw_n64_hidden_energy": mean(hidden_vals),
                "raw_n64_selected_real_utility": mean(util_vals),
                "stress_rows": len(raw_vals),
            }
        )
    write_csv(
        OUT / "v3_family_robustness.csv",
        family_rows,
        ["graph_family", "raw_n64_oracle_regret", "raw_n64_hidden_energy", "raw_n64_selected_real_utility", "stress_rows"],
    )

    repair_specs = [
        ("all_high_n", "combined_repair", "selected_real_utility"),
        ("all_high_n", "adaptive_gate", "selected_real_utility"),
        ("all_high_n", "oracle", "selected_real_utility"),
        ("hard_oracle_gap_gt_0.002", "combined_repair", "selected_real_utility"),
        ("hard_oracle_gap_gt_0.002", "adaptive_gate", "selected_real_utility"),
        ("hard_oracle_gap_gt_0.002", "oracle", "selected_real_utility"),
    ]
    repair_rows = []
    for scope, treatment, metric in repair_specs:
        row = statistical_lookup(stat_rows, scope, treatment, metric)
        repair_rows.append(
            {
                "scope": scope,
                "treatment": treatment,
                "metric": metric,
                "n_pairs": inum(row["n_pairs"]),
                "mean_delta": fnum(row["mean_delta"]),
                "ci95_low": fnum(row["ci95_low"]),
                "ci95_high": fnum(row["ci95_high"]),
            }
        )
    write_csv(
        OUT / "v3_repair_gate_summary.csv",
        repair_rows,
        ["scope", "treatment", "metric", "n_pairs", "mean_delta", "ci95_low", "ci95_high"],
    )

    learned = learned_rows[0]
    learned_summary = [
        {"metric": "train_rows", "value": inum(learned["train_rows"])},
        {"metric": "test_rows", "value": inum(learned["test_rows"])},
        {"metric": "raw_score_rank_correlation", "value": fnum(learned["raw_score_rank_correlation"])},
        {"metric": "learned_utility_rank_correlation", "value": fnum(learned["learned_utility_rank_correlation"])},
        {"metric": "mean_raw_selected_utility", "value": fnum(learned["mean_raw_selected_utility"])},
        {"metric": "mean_learned_safe_selected_utility", "value": fnum(learned["mean_learned_safe_selected_utility"])},
        {"metric": "mean_oracle_selected_utility", "value": fnum(learned["mean_oracle_selected_utility"])},
        {"metric": "hard_case_safe_gap_closed", "value": fnum(learned["hard_case_safe_gap_closed"])},
        {"metric": "safe_negative_delta_rate", "value": fnum(learned["safe_negative_delta_rate"])},
    ]
    write_csv(OUT / "v3_learned_calibration.csv", learned_summary, ["metric", "value"])

    artifacts, artifact_counts = artifact_inventory()
    write_csv(OUT / "v3_artifact_inventory.csv", artifacts, ["path", "category", "bytes"])

    # Figure 1: constraint shadow matrix.
    plt.figure(figsize=(7.2, 4.2))
    plt.imshow(matrix, aspect="auto", cmap="magma")
    plt.colorbar(label="mean raw N=64 oracle regret")
    plt.xticks(range(len(failures)), [x.replace("_", "\n") for x in failures], fontsize=7)
    plt.yticks(range(len(families)), [x.replace("_", " ") for x in families], fontsize=8)
    plt.title("Constraint-shadow matrix")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            plt.text(j, i, fmt(value, 3), ha="center", va="center", color="white", fontsize=7)
    savefig(OUT_FIGS / "v3_constraint_shadow_matrix.pdf")

    # Figure 2: repair and gate deltas.
    all_scope = [r for r in repair_rows if r["scope"] == "all_high_n"]
    hard_scope = [r for r in repair_rows if r["scope"] == "hard_oracle_gap_gt_0.002"]
    labels = [r["treatment"].replace("_", "\n") for r in all_scope]
    x = list(range(len(labels)))
    width = 0.34
    plt.figure(figsize=(7.0, 4.0))
    plt.bar([i - width / 2 for i in x], [r["mean_delta"] for r in all_scope], width, label="all N=64 pairs")
    plt.bar([i + width / 2 for i in x], [r["mean_delta"] for r in hard_scope], width, label="hard cases")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xticks(x, labels, fontsize=8)
    plt.ylabel("selected utility delta vs raw")
    plt.title("Repair and gate stress deltas")
    plt.legend(fontsize=8)
    savefig(OUT_FIGS / "v3_repair_gate_delta.pdf")

    # Figure 3: learned calibration.
    plt.figure(figsize=(6.8, 4.0))
    plt.subplot(1, 2, 1)
    plt.bar(["raw\nscore", "learned\nutility"], [fnum(learned["raw_score_rank_correlation"]), fnum(learned["learned_utility_rank_correlation"])])
    plt.ylim(0, 1)
    plt.ylabel("rank correlation")
    plt.title("Held-out alignment")
    plt.subplot(1, 2, 2)
    plt.bar(
        ["raw", "learned\nsafe", "oracle"],
        [
            fnum(learned["mean_raw_selected_utility"]),
            fnum(learned["mean_learned_safe_selected_utility"]),
            fnum(learned["mean_oracle_selected_utility"]),
        ],
    )
    plt.ylabel("mean selected utility")
    plt.title("Selected utility")
    savefig(OUT_FIGS / "v3_learned_calibration.pdf")

    # Figure 4: claim boundary inventory.
    status_counts = Counter(c["status"] for c in claims)
    plt.figure(figsize=(5.8, 3.6))
    plt.bar(list(status_counts.keys()), list(status_counts.values()), color=["#2f6f4e", "#9f4f3f"])
    plt.ylabel("claim count")
    plt.title("Claim boundary inventory")
    for idx, value in enumerate(status_counts.values()):
        plt.text(idx, value + 0.05, str(value), ha="center")
    savefig(OUT_FIGS / "v3_claim_boundary_inventory.pdf")

    # Figure 5: artifact surface.
    artifact_labels = sorted(artifact_counts)
    plt.figure(figsize=(7.0, 3.8))
    plt.bar(artifact_labels, [artifact_counts[k] for k in artifact_labels])
    plt.xticks(rotation=30, ha="right", fontsize=8)
    plt.ylabel("file count")
    plt.title("Artifact surface before v3 outputs")
    savefig(OUT_FIGS / "v3_artifact_surface.pdf")

    # Figure 6: family robustness.
    plt.figure(figsize=(7.0, 4.0))
    plt.bar([r["graph_family"].replace("_", "\n") for r in family_rows], [r["raw_n64_oracle_regret"] for r in family_rows])
    plt.ylabel("mean raw N=64 oracle regret")
    plt.title("Family-level constraint-shadow stress")
    savefig(OUT_FIGS / "v3_family_robustness.pdf")

    copy_public_figures()

    all_adaptive = statistical_lookup(stat_rows, "all_high_n", "adaptive_gate", "selected_real_utility")
    hard_adaptive = statistical_lookup(stat_rows, "hard_oracle_gap_gt_0.002", "adaptive_gate", "selected_real_utility")
    combined_all = statistical_lookup(stat_rows, "all_high_n", "combined_repair", "selected_real_utility")

    summary = {
        "supported_claims": len(supported_claims),
        "unsupported_boundaries": len(unsupported_claims),
        "claim_map_entries": len(claim_map["claims"]),
        "conditions": inum(run_summary["n_conditions"]),
        "seed_rows": inum(run_summary["n_seed_rows"]),
        "main_rows": inum(run_summary["n_main_rows"]),
        "hard_high_n_cases": inum(run_summary["n_hard_high_n_cases"]),
        "exact_law_mean_absolute_error": fnum(run_summary["exact_law_mean_absolute_error"]),
        "learned_lite_ran": bool(run_summary["learned_lite_ran"]),
        "exact_law_rows": len(exact_rows),
        "all_adaptive_gain": fnum(all_adaptive["mean_delta"]),
        "all_adaptive_ci_low": fnum(all_adaptive["ci95_low"]),
        "all_adaptive_ci_high": fnum(all_adaptive["ci95_high"]),
        "hard_adaptive_gain": fnum(hard_adaptive["mean_delta"]),
        "hard_adaptive_ci_low": fnum(hard_adaptive["ci95_low"]),
        "hard_adaptive_ci_high": fnum(hard_adaptive["ci95_high"]),
        "combined_repair_gain": fnum(combined_all["mean_delta"]),
        "learned_raw_rank": fnum(learned["raw_score_rank_correlation"]),
        "learned_utility_rank": fnum(learned["learned_utility_rank_correlation"]),
        "learned_safe_gap_closed": fnum(learned["hard_case_safe_gap_closed"]),
        "learned_safe_negative_delta_rate": fnum(learned["safe_negative_delta_rate"]),
        "families": len(families),
        "hidden_failures": len(failures),
        "artifact_files": len(artifacts),
        "v3_figures": len(list(OUT_FIGS.glob("*.pdf"))),
    }

    with (OUT / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    macros = {
        "VThreeGraphSupportedClaims": summary["supported_claims"],
        "VThreeGraphUnsupportedBoundaries": summary["unsupported_boundaries"],
        "VThreeGraphConditions": summary["conditions"],
        "VThreeGraphSeedRows": summary["seed_rows"],
        "VThreeGraphMainRows": summary["main_rows"],
        "VThreeGraphHardCases": summary["hard_high_n_cases"],
        "VThreeGraphExactError": fmt(summary["exact_law_mean_absolute_error"], 6),
        "VThreeGraphAllAdaptiveGain": fmt(summary["all_adaptive_gain"], 5),
        "VThreeGraphAllAdaptiveLow": fmt(summary["all_adaptive_ci_low"], 5),
        "VThreeGraphAllAdaptiveHigh": fmt(summary["all_adaptive_ci_high"], 5),
        "VThreeGraphHardAdaptiveGain": fmt(summary["hard_adaptive_gain"], 5),
        "VThreeGraphHardAdaptiveLow": fmt(summary["hard_adaptive_ci_low"], 5),
        "VThreeGraphHardAdaptiveHigh": fmt(summary["hard_adaptive_ci_high"], 5),
        "VThreeGraphCombinedGain": fmt(summary["combined_repair_gain"], 5),
        "VThreeGraphRawRank": fmt(summary["learned_raw_rank"], 3),
        "VThreeGraphLearnedRank": fmt(summary["learned_utility_rank"], 3),
        "VThreeGraphSafeGapClosed": fmt(summary["learned_safe_gap_closed"], 3),
        "VThreeGraphFamilies": summary["families"],
        "VThreeGraphHiddenFailures": summary["hidden_failures"],
        "VThreeGraphArtifactFiles": summary["artifact_files"],
        "VThreeGraphFigures": summary["v3_figures"],
    }
    with (PAPER_DIR / "v3_results_macros.tex").open("w", encoding="utf-8") as f:
        for name, value in macros.items():
            f.write(f"\\newcommand{{\\{name}}}{{{value}}}\n")

    print(f"v3 graph evidence complete: {OUT}")
    print(
        "claims={supported_claims} boundaries={unsupported_boundaries} "
        "conditions={conditions} artifacts={artifact_files} figures={v3_figures}".format(**summary)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
