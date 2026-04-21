# Additional Source 1 — comparison to open-source reference sources

High-level **design posture** only—not a feature matrix.

| Dimension | AS1 | Source A | Sources B–H |
|-----------|-------------------------------------|----------|-------------|
| **Primary buyer** | CSPs / large operators (commercial OSS/BSS) | Engineering / automation teams (open platform) | Mixed (open tools, varied scale) |
| **Delivery** | Licensed suite, partner-led, **managed** options | Self-hosted open source + community/apps | Self-hosted open source |
| **Inventory philosophy** | **Active**, **service-centric**, **BSS-linked** | **Intended-state** SoT + rich **network** model | B: SoT reference; C–H: narrower or different focus (see their indexes) |
| **Orchestration** | **Productized** SM-O components, adapters | **Jobs**, **hooks**, **Git**, **plugins** | Varies; rarely full SM-O |
| **Assurance** | **Native** SQM/problem management in suite | Integrate external NMS/monitoring | Source F is **monitoring-first** |
| **Standards** | **MEF**/open API **framing** in marketing | **REST**, **GraphQL**, community patterns | Varies |
| **Transparency** | **Proprietary**; no public source review | Full code auditability | Full code auditability |

## When to use AS1 in a greenfield discussion

- **Operator-scale** requirements: **BSS**, **partner ecosystem**, **SLA-driven** closed loop.
- **Regulated** telco procurement patterns (RFP-driven suites).

## When to prefer Source A patterns

- **In-house** automation ownership, **GitOps**, **plugin** velocity, and **avoiding** vendor lock-in for **inventory semantics**.
