#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode main.tex
  exit $?
fi

cat <<'MSG'
latexmk no está instalado en este entorno.

Para compilar en otra máquina con una distribución LaTeX completa, ejecutar:

  cd latex_doc
  latexmk -pdf -interaction=nonstopmode main.tex

Alternativa manual:

  pdflatex -interaction=nonstopmode main.tex
  bibtex main
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex

Este mensaje solo indica que faltó latexmk local; el documento puede compilarse en Overleaf con pdfLaTeX y BibTeX.
MSG

exit 0
