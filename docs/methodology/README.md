# Neo Angele Risk Lab methodology

This folder contains the project's technical and methodological report.

## Files

- `neo_ange_methodology.tex`: main LaTeX document.
- `build_pdf.md`: instructions for compiling the PDF.

## Quick Build

```bash
cd docs/methodology
pdflatex neo_ange_methodology.tex
```

If your LaTeX installation requires multiple passes to update the index and references:

```bash
pdflatex neo_ange_methodology.tex
pdflatex neo_ange_methodology.tex
```

From the repository root, you can also use:

```bash
bash scripts/build_methodology_pdf.sh
```

The document does not depend on external images. Mermaid diagrams are kept as `.mmd` files in `docs/diagrams` and are described inside the document.
