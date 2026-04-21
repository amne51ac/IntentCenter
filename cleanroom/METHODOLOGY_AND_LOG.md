# Methodology, instructions, and activity log

## Original instructions (paraphrased)

1. Perform a **clean room** documentation exercise.
2. Refer to the reviewed upstream codebase only as **Source Application A**, **Source A**, or **Application A**.
3. Review that codebase and **document capabilities and design** under `cleanroom/` as Markdown files.
4. Use a **subdirectory for Source A** (`cleanroom/source-a/`).
5. **Do not** share **code** or **copyrighted content**—only design, features, and high-level behavior.
6. **Keep a record** of instructions, steps, and reference notes inside `cleanroom/`.

## Constraints adopted for this folder

- **No source code** from the upstream tree (no classes, functions, or copied snippets).
- **No verbatim** documentation passages, JSON payloads, or long quotations.
- **No** file paths into the upstream repository used as copy-paste references to proprietary text.
- Factual statements (for example, technology choices named in public metadata) may be summarized in our own words.
- Design descriptions are **inferential summaries** based on public documentation structure and module organization, written independently.

## Review methodology

1. Inspect the **layout** of the cloned upstream repository: documentation tree, Django application packages, and dependency metadata.
2. Read **overview-level** user and developer documentation (section titles and conceptual explanations) without transcribing them.
3. Synthesize **capability areas**: domain models, platform services, APIs, extensibility, operations.
4. Record conclusions in **new** Markdown files under `cleanroom/source-a/`.
5. For deeper passes, use **automated enumeration** (file counts, class discovery in model modules, URL registration lists, settings such as `INSTALLED_APPS` and middleware) and **read representative modules** for behavior (middleware, plugin loader, events). **Not every file is opened by hand**; coverage is **systematic by subsystem** rather than literal per-file review.

## Activity log

| Date (UTC context) | Action |
|--------------------|--------|
| Session start | Created `cleanroom/README.md`, this log, and initial `source-a` topic files. |
| Session start | Surveyed upstream docs: user guide (administration, feature guides, core data model, platform functionality), development guides (apps, jobs, UI), and `pyproject` dependency hints for runtime stack. |
| Session start | Surveyed Django app areas under the upstream package (for example DCIM, IPAM, circuits, tenancy, extras, jobs-related apps) to align topic boundaries with actual module splits. |
| Session start | Authored eight topic Markdown files under `cleanroom/source-a/` plus `INDEX.md`, covering purpose, runtime, domain areas, extensibility, automation, APIs/events, security, and UI/operations. |
| Follow-up | Enumerated Python and text asset counts under the main package; extracted Django app list, middleware chain roles, API URL composition, and plugin extension hooks from core settings and plugin bootstrap logic; enumerated model classes via exports and class declarations per app; added `09-` through `11-` deep architecture documents and expanded `INDEX.md`. |
| Comparison pass | Cloned Sources B–H into workspace root; added `cleanroom/reference-platforms/` (`INDEX.md`, `comparison-matrix.md`, notes for B–H); updated `cleanroom/README.md`. TeemIP uses two repos: core IPAM + zone management. |
| Deep dive pass | Expanded `source-b.md`–`source-h.md` with stack-specific subsystems (NetBox: RQ/Strawberry/HTMX/plugins; phpIPAM: tools surface; Ralph: Django apps; TeemIP: iTop coupling; NAV: polling/alert subsystems; openDCIM/RackTables: PHP structure); added `source-a/12-deep-dive-cross-cutting-details.md`; updated `source-a/INDEX.md` and `reference-platforms/INDEX.md`. |
| Restructure | Moved Sources **B–H** into per-source subdirectories `cleanroom/source-b/` … `source-h/`, each with **`INDEX.md`** and **`01`–`09`** topic files (parallel to Source A’s multi-file layout). Removed monolithic `reference-platforms/source-*.md`; hub remains `reference-platforms/INDEX.md` + `comparison-matrix.md`. Updated `cleanroom/README.md`, `METHODOLOGY_AND_LOG.md`, and `source-a/INDEX.md` cross-links. |
| AS1 pass | Added `cleanroom/additional-source-1/` for **Additional Source 1** (public marketing only); updated `README`, `reference-platforms/INDEX`, `comparison-matrix`, `source-a/INDEX`, and reviewer section below. |

## Reference for reviewers

### Source A (primary target)

Clone path: `NetworkInventoryManagementSystem/nautobot/`

Re-review or expand these notes by walking the same documentation sections and app list; update this log when adding major new documents.

### Sources B–H (comparison platforms)

Shallow `git clone` into the workspace root (names match `cleanroom/reference-platforms/INDEX.md`):

| Designation | Documentation directory | Clone directory | Remote (GitHub) |
|-------------|---------------------------|-----------------|-------------------|
| **Source B** | `cleanroom/source-b/` | `netbox/` | `netbox-community/netbox` |
| **Source C** | `cleanroom/source-c/` | `phpipam/` | `phpipam/phpipam` |
| **Source D** | `cleanroom/source-d/` | `ralph/` | `allegro/ralph` (branch `ng` at clone time) |
| **Source E** | `cleanroom/source-e/` | `teemip-core-ip-mgmt/`, `teemip-zone-mgmt/` | `TeemIp/teemip-core-ip-mgmt`, `TeemIp/teemip-zone-mgmt` |
| **Source F** | `cleanroom/source-f/` | `nav/` | `Uninett/nav` |
| **Source G** | `cleanroom/source-g/` | `opendcim/` | `opendcim/opendcim` |
| **Source H** | `cleanroom/source-h/` | `racktables/` | `RackTables/racktables` |

Each directory contains **`INDEX.md`** and topic files **`01`–`09`**. Hub: `cleanroom/reference-platforms/INDEX.md`. **Source A:** `cleanroom/source-a/` (files **01–12**). No source code is copied into these docs.

### Additional Source 1 (AS1) — commercial reference (no clone)

| Designation | Documentation directory | Notes |
|-------------|---------------------------|--------|
| **AS1** | `cleanroom/additional-source-1/` | **Not** open-source. Analysis based on **public** product marketing, blogs, and analyst summaries only—files **`01`–`09`** + `INDEX.md`. |
