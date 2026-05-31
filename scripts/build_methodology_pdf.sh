#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC_DIR="$ROOT_DIR/docs/methodology"
TEX_FILE="neo_ange_methodology.tex"

cd "$DOC_DIR"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf "$TEX_FILE"
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex "$TEX_FILE"
  pdflatex "$TEX_FILE"
elif command -v xelatex >/dev/null 2>&1; then
  xelatex "$TEX_FILE"
  xelatex "$TEX_FILE"
elif command -v lualatex >/dev/null 2>&1; then
  lualatex "$TEX_FILE"
  lualatex "$TEX_FILE"
else
  echo "No LaTeX engine found. Install latexmk, pdflatex, xelatex, or lualatex."
  exit 1
fi
