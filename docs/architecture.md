# Architecture & design visuals

This document expands the [README](../README.md) with diagrams you can maintain as the platform design evolves. Diagrams use [Mermaid](https://mermaid.js.org/), which renders on GitHub. Content here describes the **target** architecture (multi-region, queues, plugin registry, etc.); the running code under `platform/` may not implement every box yet—see the root README **Implementation status** note.

---

## 1. System context (who connects to what)

Provider-scale operators, internal teams, and machines interact with the platform; northbound systems consume intent and events.

```mermaid
flowchart TB
  subgraph actors["People & operators"]
    NOC[NOC / NetOps]
    DC[Data center / field]
    Sec[Security / compliance]
  end

  subgraph machines["Automation & platforms"]
    CI[CI/CD & Git]
    Ext[External orchestrators]
    Mon[Monitoring / observability stacks]
  end

  subgraph north["Northbound & enterprise"]
    BSS[BSS / OSS / billing-adjacent]
    ITSM[ITSM / ticketing]
    IdP[Identity provider / SSO]
  end

  Platform[(Network automation & DCIM platform)]

  NOC --> Platform
  DC --> Platform
  Sec --> Platform
  CI --> Platform
  Ext --> Platform
  Mon --> Platform
  BSS --> Platform
  Platform --> ITSM
  IdP --> Platform
```

---

## 2. Logical containers (runtime view)

Stateless edge, core services, durable data, async work, and plugin workloads are separated so each tier can scale and fail independently.

```mermaid
flowchart LR
  subgraph edge["Edge & API"]
    GW[API gateway / BFF]
    REST[REST vN]
    GQL[GraphQL read]
    WS[Realtime / subscriptions]
  end

  subgraph core["Core domain services"]
    INV[Inventory & DCIM]
    IPAM[IPAM & addressing]
    CIR[Circuits & topology]
    AUTO[Automation & policies]
  end

  subgraph async["Async & integration"]
    Q[Job queue / streams]
    WRK[Workers & adapters]
    EVT[Event bus & webhooks]
  end

  subgraph data["Data plane"]
    DB[(Primary DB)]
    REP[(Read replicas)]
    OBJ[(Object store / artifacts)]
    CACHE[(Cache)]
  end

  subgraph ext["Extensibility"]
    PH[Plugin / app host]
    REG[Extension registry]
  end

  GW --> REST
  GW --> GQL
  GW --> WS
  REST --> INV
  REST --> IPAM
  REST --> CIR
  GQL --> INV
  INV --> DB
  IPAM --> DB
  CIR --> DB
  AUTO --> Q
  Q --> WRK
  WRK --> EVT
  INV --> EVT
  DB --> REP
  AUTO --> OBJ
  GW --> CACHE
  PH --> REG
  PH --> REST
```

---

## 3. Control plane vs data plane (mental model)

**Intent** (what should be true) is stored and audited in the control plane; **automation** applies changes and reconciles observed state without collapsing those concerns.

```mermaid
flowchart TB
  subgraph cp["Control plane"]
    SOT[Authoritative inventory & intent]
    POL[Policy & approvals]
    AUD[Audit & change records]
  end

  subgraph dp["Data plane execution"]
    JOBS[Jobs / workflows]
    ADP[Device & cloud adapters]
    OBS[Observed state / telemetry ingest]
  end

  subgraph ext["External reality"]
    NET[Network & infra under management]
  end

  SOT --> POL
  POL --> JOBS
  JOBS --> ADP
  ADP --> NET
  NET --> OBS
  OBS --> SOT
  JOBS --> AUD
  SOT --> AUD
```

---

## 4. Multi-region / multi-cloud deployment (reference pattern)

A typical **active/active or active/passive** layout: global routing, regional clusters, replicated data with explicit RPO/RTO.

```mermaid
flowchart TB
  subgraph global["Global"]
    DNS[DNS / global LB / traffic management]
  end

  subgraph r1["Region A — cloud or on-prem"]
    K1[Kubernetes / VM cluster]
    DB1[(Regional DB primary or replica)]
  end

  subgraph r2["Region B"]
    K2[Kubernetes / VM cluster]
    DB2[(Regional DB replica / DR)]
  end

  OBJG[(Object storage — cross-region replication)]

  DNS --> K1
  DNS --> K2
  K1 --> DB1
  K2 --> DB2
  DB1 -. replication / backup .-> DB2
  K1 --> OBJG
  K2 --> OBJG
```

---

## 5. Sequence: change request through safe automation

Illustrates **approval**, **idempotent** job execution, and **event** fan-out to integrations.

```mermaid
sequenceDiagram
  participant U as Operator / API client
  participant API as API & policy
  participant SOT as Inventory / intent
  participant Q as Job queue
  participant W as Worker / adapter
  participant T as Target infrastructure
  participant EVT as Events / webhooks

  U->>API: Propose change (REST/GraphQL)
  API->>SOT: Validate & record intent
  API->>API: Policy / approval gate
  API->>Q: Enqueue job (idempotent key)
  Q->>W: Dispatch
  W->>T: Apply change
  T-->>W: Result
  W->>SOT: Reconcile state / artifacts
  SOT->>EVT: Emit change & audit events
  EVT-->>U: Webhook / subscription notify
```

---

## 6. Plugin & app boundary

Plugins extend the UI, APIs, jobs, and validations without forking core—contracts stay versioned.

```mermaid
flowchart LR
  subgraph core["Platform core"]
    API[Stable public APIs]
    HOOKS[Hooks: GraphQL, jobs, UI slots, validators]
  end

  subgraph apps["Apps / plugins"]
    P1[Discovery pack]
    P2[Compliance pack]
    P3[Custom workflow]
  end

  P1 --> HOOKS
  P2 --> HOOKS
  P3 --> HOOKS
  HOOKS --> API
```

---

## Diagram maintenance

- Keep diagrams **technology-agnostic** until ADRs lock specific products.
- When stack choices land, add a **deployment diagram** folder (e.g. `docs/diagrams/`) with rendered PNG/SVG exports for slide decks if needed.
- Prefer **one diagram per concern** (context vs containers vs deployment) to avoid unmaintainable mega-charts.
