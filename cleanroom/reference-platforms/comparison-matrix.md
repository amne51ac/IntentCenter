# Reference platforms — comparison matrix (high level)

Rows describe **design posture**, not exhaustive feature parity. Use this to choose where to borrow concepts versus where products solve different problems.

Column **Source A** is the primary target (see [`../source-a/`](../source-a/INDEX.md)). Columns **Source B** through **Source H** match the per-source docs under [`../source-b/`](../source-b/INDEX.md) … [`../source-h/`](../source-h/INDEX.md) and this [`INDEX.md`](INDEX.md).

| Dimension | Source B | Source A | Source C | Source D | Source E | Source F | Source G | Source H |
|-----------|----------|----------|----------|----------|----------|----------|----------|----------|
| **Center of gravity** | Intended-state inventory + rich APIs | Same family + jobs, Git datasources, app ecosystem | IP addressing workflows | Hardware asset lifecycle + DC visualization | IP/DNS/CMDB on iTop platform | Live network observability + SNMP inventory | Facility and rack infrastructure | Racks, objects, cabling tables |
| **Typical deployment size** | Mid–large enterprise | Same | SMB to mid-market common | Large retail / DC operators | Orgs wanting ITSM + IPAM together | Universities, NOC teams | Small–mid DC teams | Labs to mid-size |
| **Automation story** | REST, scripts, events, plugins, config rendering | Stronger job framework + Git-sourced artifacts | REST API; lighter weight | Workflows, imports, Django admin patterns | REST/JSON per iTop/TeemIp docs | Programmatic hooks; monitoring-first | PHP app + DB | Scripting via PHP/MySQL |
| **Live monitoring** | Not native (integrate externally) | Same | Limited | Not primary | Optional discovery extensions | **Core** (polling, alerts, maps) | Optional SNMP add-ons | Not primary |
| **DDI (DNS/DHCP)** | Modeled where product includes VPN/wireless/DNS concepts; not a full BIND/DHCP server | Similar | Some DNS-related features in product scope | Not primary | **Strong** positioning with zone extension | DHCP stats / IP tools exist; not full DDI product | Not primary | Not primary |

**Takeaway:** Only **Source B** and **Source A** match the “programmable network SoT hub” pattern end-to-end. **Source F** overlaps inventory but optimizes for **operations telemetry**. **Source E** optimizes for **DDI + CMDB** on an ITSM base. **Source G** and **Source H** are narrower **physical** inventory tools. **Source C** is deliberately **minimal** IPAM.

---

## Additional Source 1 (AS1) — commercial CSP OSS/BSS (not open-source)

**AS1** documents from **public marketing only**—see [`../additional-source-1/INDEX.md`](../additional-source-1/INDEX.md). It does **not** fit the same matrix columns as A–H because it is a **proprietary suite** sold primarily to **communications service providers** with **BSS**, **service orchestration**, and **closed-loop assurance** as **packaged** capabilities.

| Dimension | AS1 (advertised posture) |
|-----------|---------------------------|
| **Center of gravity** | **Active** resource and **service** inventory integrated with **orchestration**, **activation**, and **assurance** in a **Digital OSS** suite |
| **Typical buyer** | Large **operators** / CSPs (RFP-driven procurement) |
| **Code transparency** | **None** (closed product); analysis is **not** code-based |
| **Automation story** | **Vendor-delivered** adapters, **intent-based** orchestration, **closed-loop** with AI/ML themes in public materials |
