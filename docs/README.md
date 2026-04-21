# `docs/` — specifications and GitHub Pages site

This folder holds **authoritative Markdown** (`architecture.md`, `design-llm-assistant.md`) and a **static documentation website** for GitHub Pages (`index.html`, `documentation.html`, `assets/`, `assets/screenshots/`, …).

- **Edit Markdown first** for long-form specs; the HTML pages summarize or mirror diagrams (e.g. architecture Mermaid figures) and link to the corresponding files on GitHub.
- **Styling:** `assets/site.css` matches the **IntentCenter operator console**—charcoal app chrome (`#0b0e14`), Signal Amber (`#e8b84e`), GitHub-style elevated panels, uppercase table headers, and Inter + JetBrains Mono.
- **Enable Pages:** Repository **Settings → Pages →** Branch `main`, folder **`/docs`**. The site publishes at `https://<user>.github.io/<repo>/` (for example `https://amne51ac.github.io/intentcenter/`).

Key entry points:

| Path | Role |
|------|------|
| `index.html` | Branded landing + **in-app screenshots** |
| `documentation.html` | Doc hub and links to repo sources |
| `architecture.md` / `architecture.html` | Target architecture (diagrams) |
| `design-llm-assistant.md` / `llm-assistant.html` | LLM copilot design |
| `assets/site.css`, `assets/intentcenter-logo.svg`, `assets/favicon.svg` | Shared styles and marks |
| `assets/screenshots/*.png` | Product UI reference imagery for the static site |
| `.nojekyll` | Disables Jekyll so static assets deploy cleanly |

### Custom domain

If you use a domain (e.g. **intentcenter.io**), add it under **Settings → Pages → Custom domain**, configure DNS per [GitHub Pages custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site), then enable **Enforce HTTPS**. For project sites, update root-relative paths in [`404.html`](404.html) if the repository name changes (`/intentcenter/...`).
