from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper" / "iclr"
BUILD_DIR = PAPER_DIR / "build"
FINAL_DIR = ROOT / "paper" / "final"
FINAL_PDF = FINAL_DIR / "graph world model-v3.pdf"
DESKTOP_PDF = Path.home() / "OneDrive" / "Desktop" / "graph world model-v3.pdf"


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print("==>", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def main() -> int:
    run([sys.executable, "experiments/v3_cached_evidence.py"], ROOT, os.environ.copy())

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for name in [
        "main.aux",
        "main.bbl",
        "main.blg",
        "main.log",
        "main.out",
        "main.pdf",
        "main.fdb_latexmk",
        "main.fls",
    ]:
        path = PAPER_DIR / name
        if path.exists():
            path.unlink()

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "1700000000"
    env["FORCE_SOURCE_DATE"] = "1"

    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=build", "main.tex"], PAPER_DIR, env)
    run(["bibtex", "build/main"], PAPER_DIR, env)
    for _ in range(4):
        run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=build", "main.tex"], PAPER_DIR, env)

    built = BUILD_DIR / "main.pdf"
    if not built.exists():
        raise FileNotFoundError(built)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, FINAL_PDF)
    shutil.copy2(built, DESKTOP_PDF)
    print(f"Repo PDF: {FINAL_PDF}")
    print(f"Desktop PDF: {DESKTOP_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
