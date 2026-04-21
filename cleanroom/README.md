# Clean room documentation

This directory holds **design and capability documentation** produced as a clean-room exercise. **Source Application A** (also **Source A**) is the primary automation-oriented target; **Sources B–H** are open-source comparison references; **Additional Source 1 (AS1)** documents a **commercial** CSP OSS/BSS vendor from **public** information only.

## Purpose

- Capture **features, architecture, and behavioral design** in plain language.
- **Do not** use this folder to store source code, configuration excerpts, or verbatim text from upstream copyrighted materials.

## Layout

| Path | Description |
|------|-------------|
| [`METHODOLOGY_AND_LOG.md`](METHODOLOGY_AND_LOG.md) | Instructions, constraints, clone paths, activity log. |
| [`source-a/INDEX.md`](source-a/INDEX.md) | **Source A** — full multi-file analysis (01–12). |
| [`source-b/INDEX.md`](source-b/INDEX.md) … [`source-h/INDEX.md`](source-h/INDEX.md) | **Sources B–H** — each has its own subdirectory with **01–09** topic files + index. |
| [`reference-platforms/INDEX.md`](reference-platforms/INDEX.md) | Hub linking Sources A–H + [comparison matrix](reference-platforms/comparison-matrix.md). |
| [`additional-source-1/INDEX.md`](additional-source-1/INDEX.md) | **AS1** — advertised capabilities & design (`01`–`09`). |

## Naming

- **Source A:** [`source-a/`](source-a/INDEX.md)
- **Source B–H:** [`source-b/`](source-b/INDEX.md) through [`source-h/`](source-h/INDEX.md)
- **Additional Source 1 (AS1):** [`additional-source-1/`](additional-source-1/INDEX.md) — not open-source; no clone path.

Per project convention, upstream product names are avoided in filenames where practical; letters **A–H** map to clones listed in [`METHODOLOGY_AND_LOG.md`](METHODOLOGY_AND_LOG.md).
