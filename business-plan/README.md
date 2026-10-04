# Online Business Plan — Karachi, PKR 500k, 10–15 hrs/week

**Decision:** Start **Takt Analytics** (working name), a productized *Planning & Plant Performance Control Tower* service for $10–150M manufacturers and industrial distributors in the US, UK and GCC.

The plan follows **Validate → Sell → Deliver → Improve → Scale**. Figures marked **[A]** are assumptions. Figures marked **[V]** must be checked before you rely on them (fees, tax rules and platform policies change).

## Contents

| Part | File |
|---|---|
| 1. 20 opportunities, 20 attributes each, weighted scoring | [01-opportunity-scan.md](01-opportunity-scan.md) |
| 2–3. Best 5 + stress test (customer, pain, pricing, acquisition, conversion rates) | [02-top5-stress-test.md](02-top5-stress-test.md) |
| 4. The decision + 3-scenario financial model | [03-decision-financial-model.md](03-decision-financial-model.md) |
| 5. 90-day execution plan | [04-90-day-execution-plan.md](04-90-day-execution-plan.md) |
| 6. 20 business assets (names, copy, scripts, proposal, SOPs, DAX KPI library…) | [05-business-assets.md](05-business-assets.md) |
| 7. AI & automation architecture | [06-ai-automation-architecture.md](06-ai-automation-architecture.md) |
| 8. Defensible niche / category of one | [07-competitive-advantage.md](07-competitive-advantage.md) |
| 9. Brutal reality check + top-5 risks | [08-reality-check.md](08-reality-check.md) |
| 10. First paying customer in 30 days | [09-first-revenue-challenge.md](09-first-revenue-challenge.md) |

### Working tools (`model/`)

| File | What it does |
|---|---|
| `Business_OS.xlsx` | KPI dashboard, 3 financial scenarios with live formulas, opportunity scoring, CRM pipeline with stage probabilities, 90-day tracker. Yellow cells are inputs. |
| `build_model.py` | Rebuilds the workbook and markdown tables after you change assumptions. |
| `generate_demo_data.py` | Creates a synthetic manufacturer (items, work centres, 18 months of orders, inventory, production, capacity, with a bottleneck built in) for your portfolio demo. **Never demo employer data.** |
| `profile_data.py` | Client data-readiness report (Delivery SOP step 2). |

```bash
pip install openpyxl pandas
python model/build_model.py          # regenerate model + workbook
python model/generate_demo_data.py   # demo dataset -> model/demo_data/
python model/profile_data.py model/demo_data
```

---

## FINAL RECOMMENDATION

| | |
|---|---|
| **Business** | Takt Analytics: a productized *Planning & Plant Performance Control Tower* service (Diagnostic → Build → monthly "Planning Analyst-as-a-Service" retainer) |
| **Target customer** | VP/Director of Operations or Supply Chain at $10–150M (50–500 employee) discrete/light-process manufacturers and industrial distributors in the US, UK and KSA/UAE, running any ERP plus Microsoft 365 |
| **Problem** | The weekly S&OP/production plan is rebuilt by hand from ERP exports, so capacity overloads, excess stock and stockouts, and OTIF misses are spotted too late. Enterprise IBP is unaffordable and generalist BI freelancers don't understand planning. |
| **Offer** | 10-day Planning Health Diagnostic at **$750** (founding clients **$450**, money-back guarantee, credited against the Build) → Control Tower Build at **$2.5–3.5k** → retainer at **$600–1,200/month** |
| **Starting capital** | **PKR ~100–140k** is actually needed (peak cash drawn in all 3 scenarios). Keep PKR ~350k as a reserve and don't deploy it. |
| **Expected first revenue** | **Weeks 4–8.** Base case: Month 2, about USD 400 (PKR ~110k) from an Upwork entry project. |
| **Expected 6-month monthly revenue** | Base **PKR ~590k (≈ USD 2,100)** · Conservative PKR ~270k · Aggressive PKR ~1.47M |
| **Expected 12-month monthly revenue** | Base **PKR ~1.34M (≈ USD 4,800)** · Conservative PKR ~450k · Aggressive PKR ~3.05M |
| **Hours/week** | 10–15. Outreach takes about 60% of that in Months 1–3, and delivery takes over as clients come in. A part-time contractor joins from about Month 7 in the base case. |
| **Biggest advantage** | You are a real supply planner with IBP, capacity, SAP PP, OEE and KPI design experience who also builds Power BI. Buyers get planning logic, not just visuals. This is rare among offshore BI providers and hard for AI to replace. |
| **Biggest risk** | Not sustaining outreach volume alongside your job and EMBA. Close behind it: the trust gap with Western buyers sending data to a new Pakistan-based provider. Mitigations: a fixed daily outreach block, a fixed-price money-back entry offer, working only inside the client's tenant, case studies and ERP-partner channels. |
| **First action tomorrow** | Read your employment contract's moonlighting, IP and conflict-of-interest clauses. Then, in the same session, open your Payoneer account and count how many matching Upwork jobs were posted this week (go/no-go: 15 or more). |

## Day 1 checklist (about 2 hours)

- [ ] **(20 min)** Read your employment contract for moonlighting/outside-work, IP, confidentiality, non-compete and non-solicit clauses. Write down the constraints: industries, clients and competitors to avoid, and whether you must disclose.
- [ ] **(15 min)** Open a **Payoneer** account and link your Pakistani bank account. Ask your bank about a **Freelancer Digital Account / USD account [V]**.
- [ ] **(10 min)** Start **NTN/filer status** on FBR IRIS if you don't have it, and bookmark **PSEB** freelancer registration [V].
- [ ] **(25 min)** Create your **Upwork** account. Title: *"Supply Planning & Manufacturing Power BI Specialist (S&OP, Capacity, Inventory, OEE)"*. Leave the profile as a draft.
- [ ] **(20 min)** Search Upwork for jobs posted in the last 7 days: `"power bi" AND (inventory OR "supply chain" OR manufacturing OR production OR S&OP OR OEE)`. **Count them and save 10.** If there are fewer than 15/week, plan to put more weight on LinkedIn and partners.
- [ ] **(15 min)** Pick 3 brand names. Check each for a free `.com/.co` domain, a LinkedIn page name and a quick USPTO/UK IPO search.
- [ ] **(10 min)** Make a copy of `model/Business_OS.xlsx` in OneDrive/Google Drive and fill in week 1 of the **90-Day Tracker**.
- [ ] **(5 min)** Block your calendar for 06:30–08:00 Mon–Fri plus a 4-hour Saturday block for the next 13 weeks. Label it "Takt: non-negotiable".
