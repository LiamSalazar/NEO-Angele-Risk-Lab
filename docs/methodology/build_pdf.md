# Build the Methodology PDF

The main file is:

```text
docs/methodology/neo_ange_methodology.tex
```

## Requirements

Install a LaTeX distribution compatible with `pdflatex`, `xelatex`, or `lualatex`.

Common options:

- Linux: TeX Live.
- macOS: MacTeX or BasicTeX.
- Windows: MiKTeX or TeX Live.

## Compile with pdflatex

From the repository root:

```bash
cd docs/methodology
pdflatex neo_ange_methodology.tex
pdflatex neo_ange_methodology.tex
```

The second pass helps update the index and references.

## Compile with the Script

From the repository root:

```bash
bash scripts/build_methodology_pdf.sh
```

The script tries to use these tools in order:

1. `latexmk`
2. `pdflatex`
3. `xelatex`
4. `lualatex`

If none of them is installed, it will show a message and will not generate a PDF.

## Expected Output

```text
docs/methodology/neo_ange_methodology.pdf
```

## Diagramas Mermaid

Mermaid diagrams are in:

```text
docs/diagrams/*.mmd
```

LaTeX does not compile them directly in this project. To convert them to images, use Mermaid CLI and then include the images in the `.tex` file.
