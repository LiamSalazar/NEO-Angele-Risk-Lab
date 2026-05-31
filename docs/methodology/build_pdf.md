# Construir el PDF metodologico

El archivo principal es:

```text
docs/methodology/neo_ange_methodology.tex
```

## Requisitos

Instala una distribucion LaTeX compatible con `pdflatex`, `xelatex` o `lualatex`.

Opciones comunes:

- Linux: TeX Live.
- macOS: MacTeX o BasicTeX.
- Windows: MiKTeX o TeX Live.

## Compilar con pdflatex

Desde la raiz del repositorio:

```bash
cd docs/methodology
pdflatex neo_ange_methodology.tex
pdflatex neo_ange_methodology.tex
```

La segunda pasada ayuda a actualizar indice y referencias.

## Compilar con el script

Desde la raiz del repositorio:

```bash
bash scripts/build_methodology_pdf.sh
```

El script intenta usar, en este orden:

1. `latexmk`
2. `pdflatex`
3. `xelatex`
4. `lualatex`

Si ninguno esta instalado, mostrara un mensaje y no generara PDF.

## Salida esperada

```text
docs/methodology/neo_ange_methodology.pdf
```

## Diagramas Mermaid

Los diagramas Mermaid estan en:

```text
docs/diagrams/*.mmd
```

LaTeX no los compila directamente en este proyecto. Si quieres convertirlos a imagenes, puedes usar Mermaid CLI y luego incluir las imagenes en el `.tex`.
