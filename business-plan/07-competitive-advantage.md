# Part 8 — Competitive Advantage & "Category of One"

## The niche, in one line

> **"Lightweight IBP-as-a-Service": a supply-planner-run planning control tower for $10–150M manufacturers that have outgrown spreadsheets but will never buy SAP IBP, Kinaxis or o9.**

| Element | Definition |
|---|---|
| **Specific niche** | Mid-market discrete & light-process manufacturers and industrial distributors (50–500 employees), on any ERP + Microsoft 365 |
| **Specific customer** | VP/Director of Operations or Supply Chain who owns OTIF + inventory targets and runs a weekly S&OP/production meeting |
| **Specific problem** | The weekly plan is rebuilt manually from ERP exports; capacity overloads and inventory imbalances are seen too late |
| **Specific solution** | 10-day Diagnostic → standard Control Tower (demand vs capacity, inventory health, service, S&OP summary) on their Power BI → monthly run service with commentary and alerts |
| **Unique positioning** | "Built by planners, not dashboard designers" + "no new software, no license" + "fixed price, 10 days, money-back Diagnostic" |

## Competitive map

| Alternative | Price **[A]** | Time to value | Planning expertise | Their weakness you exploit |
|---|---|---|---|---|
| Enterprise IBP (SAP IBP, Kinaxis, o9, Anaplan) | $100k+/yr + implementation | 6–12 months | High | Unaffordable/overkill for the segment |
| Mid-market planning SaaS (Netstock, GMDH Streamline, Inventory Planner, Prediko) | $500–3,000+/mo | 1–3 months | Medium (inventory-centric) | New tool to adopt; weak on capacity/S&OP governance; needs configuring |
| ERP partner reporting | $150–200/hr (US/UK) | Varies | Low–medium | Expensive; ERP-centric, not planning-centric |
| Generalist Power BI freelancers/agencies | $25–150/hr | 2–8 weeks | Low | Pretty visuals, no RCCP/safety-stock/S&OP logic |
| Hiring an analyst/planner | $60–90k/yr (US) | 3–6 months | Varies | Cost, hiring time, key-person risk |
| **You** | $750 → $3k → $600–1,200/mo | **10 days** | **High** | — |

## Proprietary assets to build (your moat compounds with every client)

| Asset | What it is | Why it's defensible |
|---|---|---|
| **Planning Health Index (PHI)** | 8-dimension, 0–100 planning maturity score with fixed scoring bands | A named, repeatable method; buyers can quote it internally; becomes the hook for the free scorecard lead magnet |
| **PHI benchmark database** | Anonymised PHI scores + KPIs from every Diagnostic, by industry & size | After 20–30 Diagnostics you can say "your excess stock is in the worst quartile for US packaging manufacturers" — no freelancer has that data |
| **Control Tower Data Model v1** | Standard star schema + 60+ DAX measures + QA tests | Cuts build time ~40%; consistent quality; contractor-deliverable |
| **ERP mapping kits** | Export guides + column maps for SAP B1, Business Central, Odoo, NetSuite, Epicor, ECC | Removes the #1 client objection ("our data is messy/hard to get") |
| **Planning engine scripts** | Python: ABC/XYZ, service-level safety stock, ROP/MOQ rounding, RCCP | IP you reuse; later the core of a micro-SaaS |
| **S&OP meeting kit** | Agenda, pre-read template, decision log | Embeds you in the client's management rhythm |

## Switching costs (ethical ones)

1. **Process embedding** — the client's weekly S&OP meeting runs on your pack and your commentary format.
2. **History** — 12+ months of KPI trend and decision log live in the model you maintain.
3. **Custom logic** — client-specific parameters (target cover, capacity calendars, exception rules) tuned over time.
4. **Benchmarks** — quarterly PHI re-score vs peers is only available while subscribed.

Client always owns their data and dashboards (say so in the contract — it *raises* trust and conversion).

## Recurring revenue design

| Layer | Price | Trigger |
|---|---|---|
| Retainer Lite | $600/mo | Default after Build |
| Retainer Pro | $1,200/mo | When client wants you in the S&OP pre-read and alerts |
| Quarterly PHI re-score + benchmark | included in Pro; $300 standalone | Board/owner reporting |
| Additional plant/entity | +$250/mo | Expansion revenue |
| Future: self-serve PHI scorecard + Power BI app template | $99–299/mo | Year 2 micro-SaaS from the standard model |

## Evolution path (service → product)

| Stage | Months | Revenue model | Your role |
|---|---|---|---|
| 1. Productized service | 0–6 | Diagnostic + Build | Do everything |
| 2. Recurring service | 6–12 | Retainers ≥ 50% of revenue | Sell + client lead; contractor delivers |
| 3. Platform-assisted service | 12–24 | Retainers + template licensing to ERP partners | Product owner + key accounts |
| 4. Micro-SaaS (optional) | 24+ | PHI scorecard + planning engine as SaaS | Founder |
