# Documento LaTeX

Esta carpeta contiene la entrega académica final de Neo Angele Risk Lab.

Archivos principales:

- `main.tex`: documento técnico académico.
- `references.bib`: bibliografía BibTeX.
- `figures/`: figuras locales necesarias para compilar.
- `tables/`: tablas auxiliares incluidas desde `main.tex`.
- `build_pdf.sh`: script de compilación tolerante a entornos sin LaTeX.

Compilación recomendada en una máquina con LaTeX:

```bash
cd latex_doc
bash build_pdf.sh
```

Si `latexmk` no está instalado, el script muestra la secuencia alternativa con `pdflatex` y `bibtex`.
