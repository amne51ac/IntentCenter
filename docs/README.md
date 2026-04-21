# `docs/` — specifications and GitHub Pages site

This folder holds **authoritative Markdown** (`architecture.md`, `design-llm-assistant.md`, `PUBLISHING.md`) and a **static documentation website** for GitHub Pages (`index.html`, `documentation.html`, `assets/`, …).

- **Edit Markdown first** for long-form specs; the HTML pages summarize or mirror diagrams (e.g. architecture Mermaid figures) and link to the corresponding files on GitHub.
- **Enable Pages:** Repository **Settings → Pages →** Branch `main`, folder **`/docs`**. The site publishes at `https://<user>.github.io/<repo>/` (see `PUBLISHING.md`).

Key entry points:

| Path | Role |
|------|------|
| `index.html` | Branded landing page |
| `documentation.html` | Doc hub and links to repo sources |
| `architecture.md` / `architecture.html` | Target architecture (diagrams) |
| `design-llm-assistant.md` / `llm-assistant.html` | LLM copilot design |
| `assets/site.css`, `assets/intentcenter-logo.svg`, `assets/favicon.svg` | Shared styles and marks |
| `.nojekyll` | Disables Jekyll so static assets deploy cleanly |
