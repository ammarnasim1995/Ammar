# Part 7 — AI & Automation Architecture

**Design principle:** automate everything that is *repeatable and low-judgement*; keep humans (you) on diagnosis, client conversations and final sign-off on numbers. Target: your hours per Diagnostic 15 → 8, per monthly retainer pack 6 → 2, per week on prospecting admin 4 → 1.

## Automation map

| Process | Manual today | Automated with | Human step left | Hours saved / month (at 4 clients) |
|---|---|---|---|---|
| Lead list building | Searching LinkedIn one by one | Sales Navigator saved searches → export via Apollo; Python dedupe/scoring vs ICP | Approve list (10 min/week) | 6 |
| Personalisation | Writing first lines | Claude: given company site + LinkedIn post + job ad → 1-line trigger + pain hypothesis (batch prompt over CSV) | Spot-check 20% | 5 |
| Cold email sending & follow-up | Gmail/Outlook by hand | Instantly (sequences, warm-up, rotation) | Reply handling | 6 |
| Reply → CRM | Copy/paste | Zapier/Make: Instantly "interested" → HubSpot/Sheet row + Teams/Slack ping | Book call | 2 |
| Upwork proposals | Writing from scratch | Proposal library (10 variants) + Claude project with your case studies → draft in 2 min | Edit & submit | 5 |
| Call notes → proposal | Typing proposals | Teams/Zoom transcript → Claude → filled proposal template (Part 6 §13) | Review pricing | 3 |
| Onboarding | Emails, folders | Make: payment email (Payoneer) → create SharePoint folder from template → send welcome + data request + kick-off booking | Kick-off call | 2 |
| Data profiling | Eyeballing exports | `model/profile_data.py` (pandas) → readiness report | Read & send | 3 |
| Model build | Rebuilding each time | Power BI template (.pbit) on the standard Control Tower Data Model; Power Query parameters for file paths/ERP mapping | Mapping tweaks | 15 |
| QA | Manual checks | DAX "test" measures (row reconciliation, KPI tie-out), Tabular Editor Best Practice Analyzer rules | Approve | 3 |
| Monthly commentary | Writing exec summary | Export KPI tables (Power BI REST `executeQueries` or Analyze-in-Excel) → Claude prompt with KPI dictionary + last month's commentary → draft | Edit (15 min) | 8 |
| Pack distribution | Screenshots + email | Power BI subscriptions / Power Automate "export to PDF" (needs Premium/Fabric capacity on client side **[V]**) or Teams post | None | 2 |
| Exception alerts (Pro retainer) | Nothing | Power BI data alerts / Power Automate on threshold (e.g., Load % > 100%, cover < lead time on A items) | None | n/a (value-add) |
| Invoicing | Manual | Recurring invoice reminder in Make on 1st of month → Payoneer request created manually (no public API for individuals **[A]**) → register row in Sheet | 2 min/invoice | 1 |
| Business KPI dashboard | Counting | `Business_OS.xlsx` formulas (or Power BI on the CRM sheet) | Sunday review | 2 |
| Content | Writing posts | Claude: turn each anonymised Diagnostic insight into 2 LinkedIn posts; Canva templates for charts | Edit & post | 4 |
| Contractor management | Ad-hoc | Loom SOPs + task board (Planner/ClickUp free) + QA checklist | Weekly review | 3 |

**Total ≈ 70 hours/month saved at 4 active clients** — the difference between needing 30 hrs/week and fitting in 15.

## Architecture

```
            ┌───────────────────────── ACQUISITION ─────────────────────────┐
 Sales Nav ─► Apollo export ─► Python (dedupe, ICP score) ─► Claude (first lines)
                                                                     │
                                                                     ▼
 Upwork alerts ─► Claude proposal draft ─► you ─► submit       Instantly sequences
                                                                     │ replies
 Tally "Planning Health Scorecard" (lead magnet) ──────┐             ▼
                                                       └──► Make/Zapier ─► CRM (HubSpot Free or Business_OS.xlsx)
                                                                          │  Teams/Slack ping
                                                                          ▼
            ┌───────────────────────── SALES ─────────────────────────────┐
  MS Bookings call ─► Teams transcript ─► Claude ─► Proposal (Word template) ─► Payoneer request
                                                                          │ payment email
            ┌───────────────────────── DELIVERY ──────────────────────────▼┐
  Make: create SharePoint client folder + welcome + data request pack
  Client uploads exports ─► profile_data.py ─► readiness report
  Power BI .pbit (standard data model + DAX library) ─► client tenant workspace
  Claude Code: Power Query/DAX refactors, Python safety-stock engine, QA scripts
            ┌───────────────────────── RUN (retainer) ─────────────────────┐
  Scheduled refresh ─► KPI export ─► Claude commentary draft ─► you edit ─► PDF/Teams pack
  Power Automate alerts on thresholds ─► client + you
            ┌───────────────────────── BACK OFFICE ────────────────────────┐
  Invoice register (Sheet) · Business_OS KPI dashboard · Sunday review
```

## Tool stack & cost

| Layer | Tool | Cost/month **[V]** | Why |
|---|---|---|---|
| AI assistant | Claude Pro (Projects with your KPI dictionary, case studies, proposal library) | ~$20 | Drafting, analysis, commentary |
| Coding | Claude Code (included in Claude Pro/Max plans **[V]**) | — | Python scripts, DAX/M refactors, data generators |
| Second opinion / Google ecosystem | ChatGPT / Gemini free tiers | $0 | Cross-check, image generation |
| BI | Power BI Desktop (free) + Power BI Pro | ~$14 | Publishing demos; client work happens in *their* tenant |
| Email/calendar/files | Microsoft 365 Business Basic | ~$6 | Matches client stack (Teams, SharePoint, Bookings) |
| Workflow | Make (free → Core) or Power Automate (included in M365 for standard connectors) | $0–11 | Onboarding, CRM, alerts |
| Cold email | Instantly + 2 secondary domains + 2–3 inboxes | ~$37 + ~$20 | Deliverability protection of main domain |
| Data | Apollo (free → Basic) | $0–49 | Contacts/emails |
| CRM | HubSpot Free or Business_OS.xlsx | $0 | Pipeline |
| Forms | Tally | $0 | Intake, scorecard, feedback |
| Video | Loom free | $0 | Demos, SOPs |
| **Total** | | **~$100–160** | |

## Claude prompts (save in a Claude Project)

**1. Personalised first line (batch over CSV)**
> You are a supply-planning consultant writing to an operations leader. For each row (company, website summary, recent LinkedIn post, open job titles), write ONE sentence (≤25 words) that references a specific, verifiable trigger and links it to a planning pain (capacity, inventory, OTIF, spreadsheet effort). No flattery, no "I hope this finds you well". If no trigger exists, return "NO_TRIGGER". Output CSV: company, first_line, trigger_type.

**2. Monthly commentary**
> Using the KPI table below (current month, prior month, target, 3-month trend) and the KPI dictionary, write a ≤200-word executive summary for a VP Operations: 3 bullets on what changed and why (use only causes evidenced in the data — flag hypotheses as hypotheses), 3 recommended actions with owner role and due date, 1 risk for next month. Do not invent numbers. Mark any value you cannot verify with [CHECK].

**3. Upwork proposal**
> Job post: [paste]. Using my profile, case studies and proposal library, draft a proposal ≤150 words: line 1 restates their problem in their words; line 2 a specific approach with their data/ERP; line 3 one relevant proof point; line 4 a question that shows expertise; close with a 10-day fixed-price option. No generic claims.

**4. Diagnostic findings**
> Given these analysis outputs (ABC/XYZ table, cover vs target, excess list, load % by work centre, OTIF Pareto), produce the Top-5 opportunities: each with finding, evidence (numbers), $ impact estimate with explicit assumption, recommended action, effort (L/M/H). Rank by $ impact ÷ effort.

## Guardrails

- **Client data never goes into consumer AI chats.** Use only aggregated KPI tables (no customer names/prices) in Claude prompts, or use a Claude Team/Enterprise or API arrangement with appropriate data terms, and state this in your NDA/DPA. Ask permission in the proposal ("we may use AI tools on aggregated, anonymised KPI outputs").
- Every AI-drafted number is tied back to the dashboard before sending.
- Don't automate LinkedIn actions with bots/extensions — LinkedIn restricts accounts for automation; your profile is your main asset.
