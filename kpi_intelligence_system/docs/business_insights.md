# Business Insights Summary

This document links each KPI to the **decisions it enables** for an
operations / strategy leader at a multi-site manufacturing organization.

## The OEE stack — Availability × Performance × Quality

| Component | Measures | When it breaks, you should… |
|---|---|---|
| **Availability** | Share of planned production time spent actually running | Run a Pareto on downtime reasons; tighten PM schedule; staff changeover faster |
| **Performance** | Throughput vs theoretical max given run time | Audit cycle times; remove micro-stops; coach on operator variance by shift |
| **Quality** | First-pass accepted units | SPC at the bottleneck station; 5-Why the top defect mode |
| **OEE** | Combined effectiveness | World-class benchmark ~85%; 60–75% is typical, often with ~10 point upside |

OEE is the headline KPI because it ties directly to **revenue per hour of asset capacity**. Moving OEE 10 points on a plant running at $10M/yr revenue translates roughly to $1.0–1.4M of incremental contribution margin, depending on cost structure.

## Cost per unit
The cleanest proxy for **operational leverage**. Watched weekly, cost/unit reveals:
- Cost inflation creeping in (material or labor)
- Wasted overhead absorption on under-utilized lines
- Plants where scaling volume will dilute fixed cost the most

When cost/unit drifts above target, the recommendation engine suggests staffing rebalancing, supplier renegotiation, or overhead reallocation.

## Yield and defect rate
Yield is a **compounder**. A 1-point first-pass yield gain:
- Reduces scrap + rework labor
- Frees downstream capacity
- Improves customer NPS (fewer returns)

Defect rate is the inverse lens — use it to focus Six Sigma efforts on the one station that causes the most pain.

## Downtime analysis (Pareto)
The 80/20 rule applies almost perfectly on the shop floor. Across most plants, 2–3 reasons typically explain 80% of downtime minutes. The dashboard's Pareto page makes this visual and actionable. The recommendation engine points operations leaders directly at the top reason per plant.

## Variance analysis
Comparing actuals vs target at every grain (plant, line, machine, day) exposes where intervention pays off most. The API's `/analytics/variance` endpoint returns rows sorted worst-first so teams can tackle high-impact items without hunting.

## Forecasting
Trend forecasting (Holt-Winters with a linear fallback) projects KPIs 2–4 weeks forward. Business value:
- Early warning of deteriorating trends before monthly business reviews
- Input to capacity planning (will the plant hit volume commitments?)
- Grounding for CapEx discussions (is PM investment reducing downtime trajectory?)

## Anomaly detection
Z-score + IsolationForest flag unusual values that thresholds alone would miss (e.g. KPI degrades slowly but the rate of change spikes). Useful for:
- Catching sensor/data-quality issues before they contaminate reports
- Detecting shift-specific or day-of-week patterns that deserve targeted intervention

## Plant benchmarking
Cross-plant ranking with quartiles + gap-to-best exposes **internal best practice**. A plant that's top-quartile on availability but bottom-quartile on cost has clear knowledge transfer opportunities both in and out. Benchmarking replaces opinions with data in leadership conversations.

## Recommendation engine
Rule-based recommendations translate KPI breaches into **specific, prioritized actions** a plant manager can execute tomorrow. Because the rules are transparent (not an LLM black box), business stakeholders trust them — and they can easily be extended or overridden.

## Closing the loop
The full decision loop the system supports:

1. **Measure** — ETL loads a consistent fact model across all plants
2. **Monitor** — Dashboard tiles + alerts surface issues in near-real-time
3. **Diagnose** — Pareto + drill-down + variance find the root cause
4. **Predict** — Forecast + anomaly detection say where it's heading
5. **Decide** — Benchmark + recommendations say what to do
6. **Verify** — Next refresh confirms whether the action worked

That closed loop is what turns this from a reporting tool into a **performance management system**.
