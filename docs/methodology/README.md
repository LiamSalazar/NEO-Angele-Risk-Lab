# Neo Angele Risk Lab methodology

Esta carpeta contiene la memoria tecnica/metodologica del proyecto.

## Archivos

- `neo_ange_methodology.tex`: documento LaTeX principal.
- `build_pdf.md`: instrucciones para compilar a PDF.

## Compilacion rapida

```bash
cd docs/methodology
pdflatex neo_ange_methodology.tex
```

Si tu instalacion de LaTeX requiere varias pasadas para actualizar indice y referencias:

```bash
pdflatex neo_ange_methodology.tex
pdflatex neo_ange_methodology.tex
```

Desde la raiz del repositorio tambien puedes usar:

```bash
bash scripts/build_methodology_pdf.sh
```

El documento no depende de imagenes externas. Los diagramas Mermaid se conservan como archivos `.mmd` en `docs/diagrams` y se describen dentro del documento.
