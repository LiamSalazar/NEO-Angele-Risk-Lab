# Neo Angele Risk Lab: documento LaTeX

Esta carpeta contiene la entrega académica en LaTeX lista para subirse a Overleaf. Es autocontenida: las figuras usadas por el documento están en `figures/`, las tablas externas están en `tables/`, la bibliografía está en `references.bib` y el archivo principal es `main.tex`.

## Uso en Overleaf

1. Comprimir únicamente la carpeta `latex_doc/` como archivo ZIP.
2. Crear un proyecto nuevo en Overleaf.
3. Subir el ZIP al proyecto.
4. Seleccionar `main.tex` como archivo principal.
5. Usar `pdfLaTeX` como compilador.
6. Compilar.

Si Overleaf no detecta `main.tex` automáticamente, abrir el menú del proyecto, entrar a la configuración del documento principal y seleccionar `main.tex`.

No es necesario subir `artifacts/`: el documento no depende de esa carpeta. Todas las figuras necesarias están en `latex_doc/figures/` y todas las tablas necesarias están en `latex_doc/tables/`.

## Compatibilidad

- Compilador recomendado: `pdfLaTeX`.
- Bibliografía: BibTeX tradicional con `references.bib`.
- No requiere `shell-escape`.
- No usa `minted`.
- Usa `listings` para bloques de código.
- Todas las figuras y tablas necesarias están dentro de esta carpeta.
- No depende de rutas absolutas ni de archivos externos al ZIP.

## Compilación local opcional

En una máquina con LaTeX instalado:

```bash
cd latex_doc
bash build_pdf.sh
```

El script intenta usar `latexmk`. Si no existe, muestra la secuencia equivalente con `pdflatex` y `bibtex`.
