# Part 5 — 90-Day Execution Plan

**Operating rhythm (10–15 hrs/week):** Mon–Fri 06:30–08:00 or 21:30–23:00 PKT (≈1.5 hrs/day = 7.5 hrs) + Saturday 4–5 hrs block + Sunday 1 hr weekly review. US East Coast business hours overlap with Karachi evening (18:00–02:00 PKT); UK overlaps 13:00–21:00 PKT; GCC overlaps almost fully. Book discovery calls Tue/Thu 19:00–21:00 PKT (= 10:00–12:00 ET, 15:00–17:00 UK).

**Non-negotiables before Day 1**
1. Read your employment contract for moonlighting, conflict-of-interest, IP and non-solicit clauses. Do not target your employer's customers, competitors or suppliers; never use employer data, files, templates or screenshots. If the contract requires disclosure, disclose.
2. Every demo, template and dataset you show is **synthetic** (generator provided in `model/generate_demo_data.py`).

---

## Days 1–7 — Foundation (≈14 hrs)

| Day | Time | Tasks | Output |
|---|---|---|---|
| **1 (Mon)** | 2 h | (1) Contract check (above). (2) Open **Payoneer** account (free) and link your PKR bank account; start a **Freelancer Digital Account** request at your bank **[V]** to retain part of proceeds in USD. (3) Create **Upwork** profile skeleton (title: *"Supply Planning & Manufacturing Power BI Specialist — S&OP, Capacity, Inventory, OEE"*). (4) Shortlist 3 brand names; check domain + LinkedIn page + USPTO/UKIPO quick search. | Accounts in review; brand shortlist |
| **2 (Tue)** | 2 h | Customer research: read 30 Upwork job posts with "Power BI" + (inventory / production / manufacturing / supply chain / S&OP / OEE). Paste them into Claude and extract: pains, words used, budgets, data sources (ERP), deliverables. Do the same for 15 LinkedIn posts by ops directors complaining about Excel planning. | `research/voice-of-customer.md` — top 10 pains in *their* words |
| **3 (Wed)** | 2 h | Offer & pricing: finalise 3 packages + retainer (Part 6 §5–6). Write the Diagnostic scope (deliverables, data needed, timeline, exclusions). Set founding-client price ($450 for first 3). | One-page offer sheet |
| **4 (Thu)** | 2 h | Demo build part 1: run `generate_demo_data.py`; load into Power BI; build star schema + measures from the DAX library (Part 6 §19). | Working data model |
| **5 (Fri)** | 1.5 h | Branding: logo (Canva, text-only), colour palette, LinkedIn banner, slide template. Buy domain (~USD 12/yr). Set up **Microsoft 365 Business Basic** (USD 6/mo) for `you@domain` + Bookings for calendar. | Domain + professional email live |
| **6 (Sat)** | 4 h | Demo build part 2: 4 pages — S&OP Summary, Demand vs Capacity (RCCP), Inventory Health, Service/OTIF — plus Planning Health Index page. Record a 4-minute **Loom** walkthrough. Publish screenshots. | Demo dashboard + Loom video |
| **7 (Sun)** | 1.5 h | Landing page on Framer/Carrd (copy in Part 6 §7), with Bookings link and Tally intake form. Rewrite LinkedIn profile (Part 6 §8). Complete Upwork profile + portfolio items (3 demo screenshots + Loom). Weekly review in tracker. | Site live, profiles live |

**Day 7 exit criteria:** Site + email + Upwork + LinkedIn + Payoneer live; demo video recorded; offer sheet done. If any item is missing, do not start outreach until it is done — but do not spend more than 3 extra days polishing.

---

## Days 8–30 — Customer acquisition system

### Who to contact (ICP)

| Attribute | Filter |
|---|---|
| Industry | Industrial machinery & components, packaging, plastics, metal fabrication, building materials, food & beverage manufacturing/co-packing, chemicals (specialty), industrial distribution |
| Size | 50–500 employees (≈ $10–150M revenue) |
| Geography | US (start with Midwest/South-East), UK, KSA/UAE |
| Titles | VP/Director Operations, Head of Supply Chain, Supply Chain Manager, Planning Manager, Plant Manager, Operations Excellence Manager, COO; CFO at < 150 employees |
| Triggers (priority) | Hiring a "demand/supply planner" or "Power BI analyst"; new ERP go-live/migration; new plant/line; posts about stockouts, overtime, OTIF penalties; recent PE acquisition |

### Where to find them

| Source | Use | Cost |
|---|---|---|
| LinkedIn Sales Navigator (start with free trial **[V]**) | Saved lead lists by title + industry + headcount + geography; "posted on LinkedIn in past 30 days" filter | ~USD 100/mo after trial |
| Apollo.io free/basic | Emails for cold email list | Free → ~USD 49/mo |
| Job boards (Indeed, LinkedIn Jobs) | Companies hiring planners/BI analysts = budget + pain signal | Free |
| ERP partner directories (Microsoft AppSource, SAP partner finder, Odoo partners) | Partner channel list | Free |
| Upwork saved searches | Inbound jobs | Connects ~USD 0.15 each **[V]** |

### Daily activity quota (≈ 1.5 hrs/day)

| Activity | Daily | Weekly | Notes |
|---|---|---|---|
| LinkedIn connection requests (ICP, personalised or blank) | 20 | 100 | Stay under ~100/week limit **[V]** |
| LinkedIn first DMs to new accepts | all accepts | ~30–40 | Message 1 in Part 6 §9 |
| Cold emails (from secondary domains, after 14-day warm-up) | 30 (from Day 22) | 150 | Max 30–40/inbox/day |
| Upwork proposals | 2–3 | 12–15 | Only jobs that mention manufacturing/inventory/supply/production |
| Partner outreach (ERP/BI agencies) | 3 | 15 | Script in Part 6 §10b |
| LinkedIn post | — | 2 | 1 teardown/insight + 1 demo clip |
| Follow-ups | as scheduled | — | See cadence |

### Follow-up schedule

| Day | LinkedIn | Cold email |
|---|---|---|
| 0 | Connection request | Email 1 (problem + Loom) |
| 1–3 | On accept: DM 1 (no pitch, question) | — |
| +3 | — | Email 2 (short bump + 1 insight) |
| +5 | DM 2 (value: 1-page "5 planning KPIs most SMEs get wrong" PDF) | — |
| +7 | — | Email 3 (case/demo angle) |
| +12 | DM 3 (direct offer: Diagnostic) | Email 4 (break-up) |
| +45 | Move to nurture; re-engage with new case study | Re-engage with new trigger |

### CRM structure (`model/Business_OS.xlsx → CRM Pipeline`, or HubSpot Free)

Fields: Lead ID · Company · Country · Industry · Revenue band · ERP · Contact · Title · LinkedIn URL · Email · Source · Trigger/hook · **Stage** · First touch · Last touch · Next action · Next action date · Touches · Deal value · Probability (auto) · Weighted value (auto) · Notes.

Stages: `1-Identified → 2-Contacted → 3-Replied → 4-Discovery booked → 5-Diagnostic proposed → 6-Won / 7-Lost / 8-Nurture`.

### Sales process

1. **Reply → book a 25-min discovery call** (Bookings link). Send a 3-question pre-call form (ERP, pain, who attends S&OP).
2. **Discovery call** (script Part 6 §12): pain → impact in $ → current process → data availability → decision process → propose Diagnostic.
3. **Same day:** 2-page proposal (Part 6 §13) + Payoneer payment link; 50% upfront for Diagnostic (100% for founding clients at $450).
4. **Kick-off within 48 h of payment**; data request template sent.
5. **Diagnostic readout call** (day 10) → present Planning Health Index + top-5 opportunities → propose Build + retainer.

### Expected Days 8–30 funnel (base)

| Metric | Volume |
|---|---|
| LinkedIn requests | ~320 → ~100 accepts → ~10 replies → 3–4 calls |
| Cold emails (Days 22–30) | ~250 → 3–5 positive replies → 1–2 calls |
| Upwork proposals | ~45 → 3–5 interviews → **1–2 hires** |
| Partners contacted | ~45 → 2–3 conversations |
| **Result** | **1–2 paid engagements, 4–6 discovery calls, pipeline of ~$4–6k** |

---

## Days 31–60 — First customers, delivery, proof

| Week | Focus | Tasks |
|---|---|---|
| 5 | Deliver #1 flawlessly | Follow Delivery SOP (Part 6 §16). Over-communicate: Day-1 kick-off, Day-3 data-quality report, Day-6 preview, Day-10 readout. Keep outreach at 70% of quota. |
| 6 | Testimonial + case study | At readout ask for (1) written testimonial, (2) Upwork review / LinkedIn recommendation, (3) permission for anonymised case study. Publish case study (template Part 6 §18) on site + LinkedIn. |
| 7 | Improve offer | Analyse every call: objections, price reactions, data blockers. Tighten Diagnostic scope; add "data readiness check" as a free 15-min pre-qualification. Productize the data request into a single Excel template per ERP. |
| 8 | Raise price + automate | After 3 delivered projects: Diagnostic $450 → $750; Upwork hourly floor $35. Automate: data profiling script, PBIT template, commentary prompt, onboarding emails (Part 7). Pitch retainer to every Diagnostic/Build client. |

**Day 60 exit criteria:** ≥2 paid clients delivered, ≥2 testimonials, 1 public case study, price raised once, first retainer proposed.

---

## Days 61–90 — Scale foundations

| Area | Actions |
|---|---|
| **Recurring revenue** | Convert ≥1 client to Retainer Lite ($600). Offer retainer as default "Phase 3" in every proposal; first month discounted 25% if signed at Build sign-off. |
| **SOPs** | Write SOPs for: data intake, data profiling, model build, QA checklist (30 checks), readout, monthly pack production. Record Loom for each (that *is* the SOP). |
| **Outsourcing** | Trial a part-time junior Power BI developer (Pakistan, PKR 50–80k/month for ~40 hrs) on a paid test task using synthetic data. Contractor does refresh, formatting, QA; you do client calls, planning logic and commentary. NDA + IP assignment contract. |
| **Automation** | Make/Power Automate pipelines live for lead intake, onboarding, monthly pack generation (Part 7). |
| **Lead generation** | Shift mix to 40% Upwork / 40% outbound / 20% partners. Launch one lead magnet: free "Planning Health Scorecard" (Tally form → automated score + PDF). Post 2×/week. |
| **Hiring** | No full-time hires. Contractor only, paid per deliverable. |
| **Productization** | Freeze the **Control Tower Data Model v1** (standard star schema + 60 measures + ERP mapping sheets for B1, BC, Odoo, NetSuite). Every new client = map data to model, not build from scratch. Target: Build delivery time 40 h → 25 h. |
| **Day 90 review** | Decide using the tracker: **Double down** if ≥ USD 1,500 MRR-equivalent or ≥ 4 paying clients; **Pivot channel** if calls happen but no closes (offer/price issue) or if no calls (targeting/message issue); **Stop** only if < 3 discovery calls in 90 days after hitting activity quotas. |
