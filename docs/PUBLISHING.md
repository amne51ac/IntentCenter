# Publishing this repository to GitHub (public)

Run these commands on your machine from the project root (`untitled-dcim-and-automation-system/`). Adjust `YOUR_USER` and `YOUR_REPO`.

## One-time: initialize Git and commit

```bash
cd untitled-dcim-and-automation-system
git init
git add README.md LICENSE .gitignore cleanroom docs platform .github
git commit -m "Initial commit: cleanroom research, platform skeleton, and CI"
```

Adjust `git add` if you are publishing only a subset (e.g. cleanroom-only) before the platform implementation exists.

## Create the GitHub repository and push

### Option A — GitHub CLI (`gh`)

```bash
gh auth login   # if needed
gh repo create YOUR_REPO --public --source=. --remote=origin --push
```

### Option B — GitHub website + SSH

1. Create a **new public** empty repository (no README) under your account.
2. Then:

```bash
git remote add origin git@github.com:YOUR_USER/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Option B — HTTPS

```bash
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git branch -M main
git push -u origin main
```

After the first push, add **branch protection** and **required reviews** on `main` when collaborators join.

---

## GitHub Pages (documentation site)

The repository includes a **static site** under [`docs/`](.) (HTML, CSS, logo assets). It provides a branded landing page and a browsable documentation hub that mirrors and links to Markdown sources (`README.md`, `docs/architecture.md`, `docs/design-llm-assistant.md`, `platform/README.md`, `cleanroom/`, etc.).

### Enable Pages

1. On GitHub: **Settings → Pages**.
2. **Build and deployment → Source:** Deploy from a branch.
3. **Branch:** `main`, **Folder:** `/docs`, Save.
4. After the workflow runs, the site is available at:

   `https://<your-username>.github.io/<repository-name>/`

   For the default upstream name, that is **[https://amne51ac.github.io/untitled-dcim-and-automation-system/](https://amne51ac.github.io/untitled-dcim-and-automation-system/)**.

The empty [`.nojekyll`](.nojekyll) file disables Jekyll processing so all static files (including paths starting with `_`) are served as-is.

### Forks and renames

If you rename the repository or use a fork, update **root-relative** links in [`404.html`](404.html) (`/untitled-dcim-and-automation-system/...`) so the error page’s styles and navigation resolve correctly for arbitrary missing URLs.

### Local preview

From `docs/`, run a static server (for example `python -m http.server 8080`) and open `http://localhost:8080/` — relative asset paths match GitHub Pages for top-level pages.
