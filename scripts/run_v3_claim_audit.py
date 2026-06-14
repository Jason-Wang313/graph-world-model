from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path.home() / "OneDrive" / "Desktop"
SOURCE_MAP = DESKTOP / "PAPER_SOURCE_MAP.md"
FINAL_PDF = ROOT / "paper" / "final" / "graph world model-v3.pdf"
DESKTOP_PDF = DESKTOP / "graph world model-v3.pdf"
OLD_DESKTOP_PDF = DESKTOP / "graph world model-v2.pdf"
SUMMARY = ROOT / "results" / "v3_cached_evidence" / "summary.json"
LOG = ROOT / "paper" / "iclr" / "build" / "main.log"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_pages(path: Path) -> int:
    out = subprocess.check_output(["pdfinfo", str(path)], text=True)
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"Could not read page count for {path}")


def count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    run([sys.executable, "experiments/v3_cached_evidence.py"])
    run(["bash", "scripts/run_claim_audit.sh"])

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    require(summary["supported_claims"] >= 6, "expected at least 6 supported graph claims")
    require(summary["unsupported_boundaries"] >= 4, "expected explicit unsupported boundaries")
    require(summary["conditions"] >= 80, "condition coverage too small")
    require(summary["seed_rows"] >= 22400, "seed-level coverage too small")
    require(summary["main_rows"] >= 5600, "aggregate coverage too small")
    require(summary["hard_high_n_cases"] >= 150, "hard-case coverage too small")
    require(summary["exact_law_mean_absolute_error"] <= 0.002, "exact-law error too large")
    require(summary["all_adaptive_gain"] >= 0.006, "adaptive all-case gain too small")
    require(summary["all_adaptive_ci_low"] > 0.0, "adaptive all-case CI crosses zero")
    require(summary["hard_adaptive_gain"] >= 0.014, "adaptive hard-case gain too small")
    require(summary["hard_adaptive_ci_low"] > 0.0, "adaptive hard-case CI crosses zero")
    require(summary["combined_repair_gain"] >= 0.005, "combined repair gain too small")
    require(summary["learned_utility_rank"] >= 0.90, "learned rank alignment too weak")
    require(summary["learned_raw_rank"] < summary["learned_utility_rank"], "learned model must improve rank alignment")
    require(summary["learned_safe_gap_closed"] >= 0.55, "learned-safe hard-case gap closure too small")
    require(summary["families"] >= 5, "family coverage too small")
    require(summary["hidden_failures"] >= 5, "hidden failure coverage too small")
    require(summary["artifact_files"] >= 35, "artifact inventory too small")
    require(summary["v3_figures"] >= 6, "expected at least six v3 figures")
    require(count_rows(ROOT / "results" / "v3_cached_evidence" / "v3_claim_inventory.csv") >= 10, "claim CSV too small")
    require(count_rows(ROOT / "results" / "v3_cached_evidence" / "v3_constraint_shadow_matrix.csv") >= 25, "matrix CSV too small")

    require(FINAL_PDF.exists(), f"missing repo final PDF: {FINAL_PDF}")
    require(DESKTOP_PDF.exists(), f"missing Desktop PDF: {DESKTOP_PDF}")
    require(sha256(FINAL_PDF) == sha256(DESKTOP_PDF), "repo/Desktop PDF hashes differ")
    require(pdf_pages(FINAL_PDF) >= 25, "final PDF is below 25 pages")
    require(not OLD_DESKTOP_PDF.exists(), f"old Desktop v2 PDF still exists: {OLD_DESKTOP_PDF}")

    row = "| `graph world model-v3.pdf` | `C:\\Users\\wangz\\graph world model` | `Jason-Wang313/graph-world-model` |"
    source_text = SOURCE_MAP.read_text(encoding="utf-8")
    require(row in source_text, "source map does not point to graph world model v3")
    require("graph world model-v2.pdf" not in source_text, "source map still contains graph v2 row")

    require(LOG.exists(), "missing LaTeX log")
    log_text = LOG.read_text(encoding="utf-8", errors="replace")
    blockers = [
        "Fatal error",
        "Emergency stop",
        "LaTeX Error",
        "Undefined control sequence",
        "There were undefined references",
        "There were undefined citations",
        "Overfull",
    ]
    for blocker in blockers:
        require(blocker not in log_text, f"LaTeX blocker in log: {blocker}")

    print("graph world model v3 audit passed")
    print(f"pages={pdf_pages(FINAL_PDF)} sha256={sha256(FINAL_PDF)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
