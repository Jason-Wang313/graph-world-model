#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd "$SCRIPT_DIR/../paper/iclr" && pwd)"

pick_latexmk() {
  for candidate in latexmk latexmk.exe; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

pick_pdflatex() {
  for candidate in pdflatex.exe pdflatex; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  if [[ -n "${LATEX_BIN_DIR:-}" && -x "$LATEX_BIN_DIR/pdflatex.exe" ]]; then
    printf '%s\n' "$LATEX_BIN_DIR/pdflatex.exe"
    return 0
  fi
  return 1
}

pick_bibtex() {
  for candidate in bibtex.exe bibtex; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  if [[ -n "${LATEX_BIN_DIR:-}" && -x "$LATEX_BIN_DIR/bibtex.exe" ]]; then
    printf '%s\n' "$LATEX_BIN_DIR/bibtex.exe"
    return 0
  fi
  return 1
}

cd "$PAPER_DIR"

if LATEXMK_BIN="$(pick_latexmk)"; then
  LATEXMK_PATH="$(command -v "$LATEXMK_BIN" || true)"
  if [[ -n "$LATEXMK_PATH" ]]; then
    LATEX_BIN_DIR="$(dirname "$LATEXMK_PATH")"
  fi
  if "$LATEXMK_BIN" -v >/dev/null 2>&1; then
    if "$LATEXMK_BIN" -pdf -interaction=nonstopmode -halt-on-error main.tex; then
      exit 0
    fi
    echo "latexmk failed; falling back to pdflatex/bibtex." >&2
  else
    echo "latexmk found but unavailable; falling back to pdflatex/bibtex." >&2
  fi
fi

PDFLATEX_BIN="$(pick_pdflatex)" || {
  echo "No pdflatex executable found on PATH" >&2
  exit 1
}
BIBTEX_BIN="$(pick_bibtex)" || {
  echo "No bibtex executable found on PATH" >&2
  exit 1
}

"$PDFLATEX_BIN" -interaction=nonstopmode -halt-on-error main.tex
"$BIBTEX_BIN" main
"$PDFLATEX_BIN" -interaction=nonstopmode -halt-on-error main.tex
"$PDFLATEX_BIN" -interaction=nonstopmode -halt-on-error main.tex
