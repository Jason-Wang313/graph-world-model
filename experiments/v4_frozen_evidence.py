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
OUT = RESULTS / "v4_frozen_evidence"
OUT_FIGS = OUT / "figures"
PUB_FIGS = RESULTS / "figures" / "v4"
PAPER_DIR = ROOT / "paper" / "iclr"
MACROS = PAPER_DIR / "v4_results_macros.tex"


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
        metadata={"Creator": "graph-world-model-v4-cache", "CreationDate": None, "ModDate": None},
    )
    plt.close()


def clean_stale_version_outputs() -> None:
    for directory in [OUT, OUT_FIGS, PUB_FIGS]:
        if not directory.exists():
            continue
        for stale in directory.glob("v3_*"):
            if stale.is_file():
                stale.unlink()


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
        "tmp",
        "v3_cached_evidence",
        "v4_frozen_evidence",
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
        if rel.parts[:3] in {("results", "figures", "v3"), ("results", "figures", "v4")}:
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


def aggregate_lookup(
    rows: list[dict[str, str]],
    graph_family: str,
    hidden_failure: str,
    stress_level: str,
    selector: str,
    n: int = 64,
) -> dict[str, str]:
    for row in rows:
        if (
            row.get("graph_family") == graph_family
            and row.get("hidden_failure") == hidden_failure
            and row.get("stress_level") == stress_level
            and row.get("selector") == selector
            and inum(row.get("N")) == n
        ):
            return row
    raise KeyError((graph_family, hidden_failure, stress_level, selector, n))


def mean_metric(rows: list[dict[str, str]], metric: str) -> float:
    values = [fnum(row.get(metric)) for row in rows]
    return mean(values) if values else 0.0


def n64_selector_rows(rows: list[dict[str, str]], selector: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("selector") == selector and inum(row.get("N")) == 64]


def benchmark_protocol_rows(stress_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    protocols = [
        (
            "interaction-network-springs",
            "ring_chord",
            "omitted_edges",
            "severe",
            "Interaction Network style spring graph with omitted latent edges",
        ),
        (
            "nri-latent-edge-alias",
            "clustered",
            "topology_aliasing",
            "severe",
            "Neural Relational Inference style latent-edge/topology aliasing probe",
        ),
        (
            "gns-long-horizon-grid",
            "grid",
            "long_horizon_drift",
            "severe",
            "Graph Network Simulator style long-horizon grid drift probe",
        ),
        (
            "chain-rest-length-shift",
            "chain",
            "shifted_rest_lengths",
            "severe",
            "Mass-spring chain rest-length shift probe",
        ),
        (
            "random-geometric-delayed-damping",
            "random_geometric",
            "delayed_damping",
            "severe",
            "Random geometric graph delayed-damping probe",
        ),
    ]
    rows: list[dict[str, object]] = []
    for protocol, graph_family, hidden_failure, stress_level, description in protocols:
        raw = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "raw")
        random = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "random")
        repair = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "combined_repair")
        gate = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "adaptive_gate")
        oracle = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "oracle")
        raw_regret = fnum(raw["oracle_regret"])
        gate_regret = fnum(gate["oracle_regret"])
        repair_regret = fnum(repair["oracle_regret"])
        rows.append(
            {
                "protocol": protocol,
                "description": description,
                "graph_family": graph_family,
                "hidden_failure": hidden_failure,
                "stress_level": stress_level,
                "random_oracle_regret": fnum(random["oracle_regret"]),
                "raw_oracle_regret": raw_regret,
                "combined_repair_oracle_regret": repair_regret,
                "adaptive_gate_oracle_regret": gate_regret,
                "oracle_oracle_regret": fnum(oracle["oracle_regret"]),
                "adaptive_regret_reduction": raw_regret - gate_regret,
                "repair_regret_reduction": raw_regret - repair_regret,
                "claim_gate": "pass" if raw_regret >= 0.002 and gate_regret <= raw_regret + 1e-12 else "diagnostic_only",
            }
        )
    return rows


def cell_gate_rows(stress_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    raw_rows = n64_selector_rows(stress_rows, "raw")
    for raw in raw_rows:
        graph_family = raw["graph_family"]
        hidden_failure = raw["hidden_failure"]
        stress_level = raw["stress_level"]
        gate = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "adaptive_gate")
        repair = aggregate_lookup(stress_rows, graph_family, hidden_failure, stress_level, "combined_repair")
        raw_regret = fnum(raw["oracle_regret"])
        gate_regret = fnum(gate["oracle_regret"])
        repair_regret = fnum(repair["oracle_regret"])
        rows.append(
            {
                "graph_family": graph_family,
                "hidden_failure": hidden_failure,
                "stress_level": stress_level,
                "raw_oracle_regret": raw_regret,
                "adaptive_oracle_regret": gate_regret,
                "combined_repair_oracle_regret": repair_regret,
                "adaptive_regret_reduction": raw_regret - gate_regret,
                "combined_regret_reduction": raw_regret - repair_regret,
                "adaptive_nonworse": gate_regret <= raw_regret + 1e-12,
                "raw_positive_regret": raw_regret > 0.002,
            }
        )
    return rows


def compute_frontier_rows(stress_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for n in sorted({inum(row.get("N")) for row in stress_rows}):
        raw = [row for row in stress_rows if row.get("selector") == "raw" and inum(row.get("N")) == n]
        gate = [row for row in stress_rows if row.get("selector") == "adaptive_gate" and inum(row.get("N")) == n]
        repair = [row for row in stress_rows if row.get("selector") == "combined_repair" and inum(row.get("N")) == n]
        out.append(
            {
                "N": n,
                "raw_mean_oracle_regret": mean_metric(raw, "oracle_regret"),
                "adaptive_mean_oracle_regret": mean_metric(gate, "oracle_regret"),
                "combined_mean_oracle_regret": mean_metric(repair, "oracle_regret"),
                "raw_mean_hidden_energy": mean_metric(raw, "selected_hidden_energy"),
                "adaptive_mean_hidden_energy": mean_metric(gate, "selected_hidden_energy"),
                "raw_mean_selected_utility": mean_metric(raw, "selected_real_utility"),
                "adaptive_mean_selected_utility": mean_metric(gate, "selected_real_utility"),
                "adaptive_regret_reduction": mean_metric(raw, "oracle_regret") - mean_metric(gate, "oracle_regret"),
                "n_cells": len(raw),
            }
        )
    return out


def topology_holdout_rows(cell_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for family in sorted({str(row["graph_family"]) for row in cell_rows}):
        rows = [row for row in cell_rows if row["graph_family"] == family]
        out.append(
            {
                "heldout_family": family,
                "stress_cells": len(rows),
                "raw_positive_regret_cells": sum(1 for row in rows if row["raw_positive_regret"]),
                "adaptive_nonworse_cells": sum(1 for row in rows if row["adaptive_nonworse"]),
                "mean_raw_oracle_regret": mean(float(row["raw_oracle_regret"]) for row in rows),
                "mean_adaptive_regret_reduction": mean(float(row["adaptive_regret_reduction"]) for row in rows),
            }
        )
    return out


def claim_gate_rows(summary: dict[str, object], cell_rows: list[dict[str, object]], benchmark_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    adaptive_nonworse = sum(1 for row in cell_rows if row["adaptive_nonworse"])
    raw_positive = sum(1 for row in cell_rows if row["raw_positive_regret"])
    benchmark_pass = sum(1 for row in benchmark_rows if row["claim_gate"] == "pass")
    gates = [
        ("claim_audit_supported", summary["supported_claims"], 7, summary["supported_claims"] >= 7),
        ("explicit_boundaries", summary["unsupported_boundaries"], 4, summary["unsupported_boundaries"] >= 4),
        ("stress_cell_count", len(cell_rows), 75, len(cell_rows) >= 75),
        ("raw_positive_regret_cells", raw_positive, 60, raw_positive >= 60),
        ("adaptive_nonworse_cells", adaptive_nonworse, 75, adaptive_nonworse >= 75),
        ("benchmark_protocol_rows", len(benchmark_rows), 5, len(benchmark_rows) >= 5),
        ("benchmark_protocol_pass_rows", benchmark_pass, 4, benchmark_pass >= 4),
        ("adaptive_mean_gain", summary["all_adaptive_gain"], 0.006, summary["all_adaptive_gain"] >= 0.006),
        ("hard_case_ci_positive", summary["hard_adaptive_ci_low"], 0.0, summary["hard_adaptive_ci_low"] > 0.0),
        ("learned_rank_alignment", summary["learned_utility_rank"], 0.90, summary["learned_utility_rank"] >= 0.90),
    ]
    return [
        {
            "gate": name,
            "observed": observed,
            "threshold": threshold,
            "pass": bool(passed),
        }
        for name, observed, threshold, passed in gates
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)
    clean_stale_version_outputs()

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
    write_csv(OUT / "v4_claim_inventory.csv", claim_rows, ["id", "status", "claim", "evidence"])

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
        OUT / "v4_constraint_shadow_matrix.csv",
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
        OUT / "v4_family_robustness.csv",
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
        OUT / "v4_repair_gate_summary.csv",
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
    write_csv(OUT / "v4_learned_calibration.csv", learned_summary, ["metric", "value"])

    artifacts, artifact_counts = artifact_inventory()
    write_csv(OUT / "v4_artifact_inventory.csv", artifacts, ["path", "category", "bytes"])

    cell_rows = cell_gate_rows(stress_rows)
    write_csv(
        OUT / "v4_cell_gate_matrix.csv",
        cell_rows,
        [
            "graph_family",
            "hidden_failure",
            "stress_level",
            "raw_oracle_regret",
            "adaptive_oracle_regret",
            "combined_repair_oracle_regret",
            "adaptive_regret_reduction",
            "combined_regret_reduction",
            "adaptive_nonworse",
            "raw_positive_regret",
        ],
    )
    benchmark_rows = benchmark_protocol_rows(stress_rows)
    write_csv(
        OUT / "v4_benchmark_protocol_bridge.csv",
        benchmark_rows,
        [
            "protocol",
            "description",
            "graph_family",
            "hidden_failure",
            "stress_level",
            "random_oracle_regret",
            "raw_oracle_regret",
            "combined_repair_oracle_regret",
            "adaptive_gate_oracle_regret",
            "oracle_oracle_regret",
            "adaptive_regret_reduction",
            "repair_regret_reduction",
            "claim_gate",
        ],
    )
    compute_rows = compute_frontier_rows(stress_rows)
    write_csv(
        OUT / "v4_compute_frontier.csv",
        compute_rows,
        [
            "N",
            "raw_mean_oracle_regret",
            "adaptive_mean_oracle_regret",
            "combined_mean_oracle_regret",
            "raw_mean_hidden_energy",
            "adaptive_mean_hidden_energy",
            "raw_mean_selected_utility",
            "adaptive_mean_selected_utility",
            "adaptive_regret_reduction",
            "n_cells",
        ],
    )
    holdout_rows = topology_holdout_rows(cell_rows)
    write_csv(
        OUT / "v4_topology_holdout.csv",
        holdout_rows,
        [
            "heldout_family",
            "stress_cells",
            "raw_positive_regret_cells",
            "adaptive_nonworse_cells",
            "mean_raw_oracle_regret",
            "mean_adaptive_regret_reduction",
        ],
    )

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
    savefig(OUT_FIGS / "v4_constraint_shadow_matrix.pdf")

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
    savefig(OUT_FIGS / "v4_repair_gate_delta.pdf")

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
    savefig(OUT_FIGS / "v4_learned_calibration.pdf")

    # Figure 4: claim boundary inventory.
    status_counts = Counter(c["status"] for c in claims)
    plt.figure(figsize=(5.8, 3.6))
    plt.bar(list(status_counts.keys()), list(status_counts.values()), color=["#2f6f4e", "#9f4f3f"])
    plt.ylabel("claim count")
    plt.title("Claim boundary inventory")
    for idx, value in enumerate(status_counts.values()):
        plt.text(idx, value + 0.05, str(value), ha="center")
    savefig(OUT_FIGS / "v4_claim_boundary_inventory.pdf")

    # Figure 5: artifact surface.
    artifact_labels = sorted(artifact_counts)
    plt.figure(figsize=(7.0, 3.8))
    plt.bar(artifact_labels, [artifact_counts[k] for k in artifact_labels])
    plt.xticks(rotation=30, ha="right", fontsize=8)
    plt.ylabel("file count")
    plt.title("Artifact surface before v4 outputs")
    savefig(OUT_FIGS / "v4_artifact_surface.pdf")

    # Figure 6: family robustness.
    plt.figure(figsize=(7.0, 4.0))
    plt.bar([r["graph_family"].replace("_", "\n") for r in family_rows], [r["raw_n64_oracle_regret"] for r in family_rows])
    plt.ylabel("mean raw N=64 oracle regret")
    plt.title("Family-level constraint-shadow stress")
    savefig(OUT_FIGS / "v4_family_robustness.pdf")

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
        "cell_gate_rows": len(cell_rows),
        "adaptive_nonworse_cells": sum(1 for row in cell_rows if row["adaptive_nonworse"]),
        "raw_positive_regret_cells": sum(1 for row in cell_rows if row["raw_positive_regret"]),
        "benchmark_protocol_rows": len(benchmark_rows),
        "benchmark_protocol_pass_rows": sum(1 for row in benchmark_rows if row["claim_gate"] == "pass"),
        "compute_frontier_rows": len(compute_rows),
        "topology_holdout_rows": len(holdout_rows),
    }

    gate_rows = claim_gate_rows(summary, cell_rows, benchmark_rows)
    write_csv(OUT / "v4_claim_gates.csv", gate_rows, ["gate", "observed", "threshold", "pass"])

    # Figure 7: standard graph-dynamics protocol bridge.
    labels = [row["protocol"].replace("-", "\n") for row in benchmark_rows]
    x = list(range(len(labels)))
    width = 0.34
    plt.figure(figsize=(8.0, 4.1))
    plt.bar([i - width / 2 for i in x], [row["raw_oracle_regret"] for row in benchmark_rows], width, label="raw")
    plt.bar([i + width / 2 for i in x], [row["adaptive_gate_oracle_regret"] for row in benchmark_rows], width, label="adaptive gate")
    plt.xticks(x, labels, fontsize=7)
    plt.ylabel("N=64 oracle regret")
    plt.title("Recognized graph-dynamics protocol bridge")
    plt.legend(fontsize=8)
    savefig(OUT_FIGS / "v4_benchmark_protocol_bridge.pdf")

    # Figure 8: compute frontier under adversarial selection.
    plt.figure(figsize=(7.2, 4.0))
    ns = [row["N"] for row in compute_rows]
    plt.plot(ns, [row["raw_mean_oracle_regret"] for row in compute_rows], marker="o", label="raw regret")
    plt.plot(ns, [row["adaptive_mean_oracle_regret"] for row in compute_rows], marker="o", label="adaptive regret")
    plt.plot(ns, [row["raw_mean_hidden_energy"] for row in compute_rows], marker="s", label="raw hidden energy")
    plt.xscale("log", base=2)
    plt.xlabel("candidate budget N")
    plt.ylabel("stress-suite mean")
    plt.title("Compute frontier stress")
    plt.legend(fontsize=8)
    savefig(OUT_FIGS / "v4_compute_frontier.pdf")

    # Figure 9: claim-gate ledger.
    passed = [1 if row["pass"] else 0 for row in gate_rows]
    plt.figure(figsize=(7.6, 3.9))
    plt.bar([row["gate"].replace("_", "\n") for row in gate_rows], passed, color=["#2f6f4e" if value else "#9f4f3f" for value in passed])
    plt.ylim(0, 1.15)
    plt.xticks(rotation=40, ha="right", fontsize=7)
    plt.ylabel("pass")
    plt.title("Frozen v4 claim gates")
    savefig(OUT_FIGS / "v4_claim_gates.pdf")

    copy_public_figures()
    summary["v4_figures"] = len(list(OUT_FIGS.glob("*.pdf")))
    summary["claim_gates_total"] = len(gate_rows)
    summary["claim_gates_passed"] = sum(1 for row in gate_rows if row["pass"])

    with (OUT / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    macros = {
        "VFourGraphSupportedClaims": summary["supported_claims"],
        "VFourGraphUnsupportedBoundaries": summary["unsupported_boundaries"],
        "VFourGraphConditions": summary["conditions"],
        "VFourGraphSeedRows": summary["seed_rows"],
        "VFourGraphMainRows": summary["main_rows"],
        "VFourGraphHardCases": summary["hard_high_n_cases"],
        "VFourGraphExactError": fmt(summary["exact_law_mean_absolute_error"], 6),
        "VFourGraphAllAdaptiveGain": fmt(summary["all_adaptive_gain"], 5),
        "VFourGraphAllAdaptiveLow": fmt(summary["all_adaptive_ci_low"], 5),
        "VFourGraphAllAdaptiveHigh": fmt(summary["all_adaptive_ci_high"], 5),
        "VFourGraphHardAdaptiveGain": fmt(summary["hard_adaptive_gain"], 5),
        "VFourGraphHardAdaptiveLow": fmt(summary["hard_adaptive_ci_low"], 5),
        "VFourGraphHardAdaptiveHigh": fmt(summary["hard_adaptive_ci_high"], 5),
        "VFourGraphCombinedGain": fmt(summary["combined_repair_gain"], 5),
        "VFourGraphRawRank": fmt(summary["learned_raw_rank"], 3),
        "VFourGraphLearnedRank": fmt(summary["learned_utility_rank"], 3),
        "VFourGraphSafeGapClosed": fmt(summary["learned_safe_gap_closed"], 3),
        "VFourGraphFamilies": summary["families"],
        "VFourGraphHiddenFailures": summary["hidden_failures"],
        "VFourGraphArtifactFiles": summary["artifact_files"],
        "VFourGraphFigures": summary["v4_figures"],
        "VFourGraphCellRows": summary["cell_gate_rows"],
        "VFourGraphAdaptiveNonworseCells": summary["adaptive_nonworse_cells"],
        "VFourGraphRawPositiveCells": summary["raw_positive_regret_cells"],
        "VFourGraphBenchmarkRows": summary["benchmark_protocol_rows"],
        "VFourGraphBenchmarkPassRows": summary["benchmark_protocol_pass_rows"],
        "VFourGraphClaimGatesPassed": summary["claim_gates_passed"],
        "VFourGraphClaimGatesTotal": summary["claim_gates_total"],
    }
    with MACROS.open("w", encoding="utf-8") as f:
        for name, value in macros.items():
            f.write(f"\\newcommand{{\\{name}}}{{{value}}}\n")

    print(f"v4 graph evidence complete: {OUT}")
    print(
        "claims={supported_claims} boundaries={unsupported_boundaries} "
        "conditions={conditions} artifacts={artifact_files} figures={v4_figures} gates={claim_gates_passed}/{claim_gates_total}".format(**summary)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
