"""
Synthetic demo data for the Planning Control Tower portfolio dashboard.

Never use employer or client data in demos. This script creates a fictional
$60M packaging/components manufacturer: 120 items, 8 work centres, 40
customers, 18 months of daily orders, weekly inventory snapshots, production
confirmations and weekly capacity - with realistic problems baked in
(seasonality, a bottleneck work centre, excess slow movers, late shipments).

Output: ./demo_data/*.csv  (load into Power BI, model as a star schema)
Usage:  python generate_demo_data.py [--seed 42]
"""
import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "demo_data"
START, MONTHS = date(2025, 4, 1), 18


def write(name, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name:<22}{len(rows):>8,} rows")


def main(seed):
    rnd = random.Random(seed)
    end = START + timedelta(days=int(MONTHS * 30.4))
    days = [START + timedelta(d) for d in range((end - START).days)]

    # --- dimensions
    wcs = [dict(WorkCenterID=f"WC{i:02d}", Name=n, ShiftsPerDay=s, HoursPerShift=8,
                Efficiency=e) for i, (n, s, e) in enumerate(
        [("Extrusion 1", 3, .85), ("Extrusion 2", 2, .80), ("Thermoforming", 2, .78),
         ("Printing", 2, .82), ("Cutting", 2, .88), ("Assembly", 1, .90),
         ("Injection Moulding", 3, .75), ("Packing", 2, .92)], 1)]
    items = []
    for i in range(1, 121):
        cls = "A" if i <= 20 else "B" if i <= 50 else "C"
        base = {"A": rnd.uniform(400, 1200), "B": rnd.uniform(80, 400), "C": rnd.uniform(5, 80)}[cls]
        items.append(dict(ItemID=f"FG{i:04d}", Description=f"Product {i:04d}", ABC=cls,
                          Family=rnd.choice(["Trays", "Lids", "Cups", "Films", "Components"]),
                          UnitCost=round(rnd.uniform(0.4, 6.0), 2), LeadTimeDays=rnd.choice([7, 10, 14, 21]),
                          TargetCoverDays={"A": 21, "B": 30, "C": 45}[cls],
                          SafetyStockQty=round(base * rnd.uniform(3, 8)),
                          PrimaryWorkCenter=rnd.choice(wcs[:7])["WorkCenterID"],
                          HoursPer1000=round(rnd.uniform(0.6, 2.5), 2), _base=base))
    custs = [dict(CustomerID=f"C{i:03d}", Name=f"Customer {i:03d}",
                  Segment=rnd.choice(["Retail", "Food service", "OEM", "Distributor"]),
                  Country=rnd.choice(["US", "US", "US", "UK", "CA"])) for i in range(1, 41)]

    # --- sales orders / shipments
    sales, so = [], 0
    bottleneck = "WC07"
    for d in days:
        if d.weekday() >= 5:
            continue
        season = 1 + 0.25 * math.sin(2 * math.pi * (d.timetuple().tm_yday - 60) / 365)
        for it in items:
            p = {"A": .9, "B": .5, "C": .12}[it["ABC"]]
            if rnd.random() > p:
                continue
            so += 1
            qty = max(1, round(rnd.gauss(it["_base"] * season, it["_base"] * .35)))
            late_p = .22 if it["PrimaryWorkCenter"] == bottleneck else .07
            on_time = 0 if rnd.random() < late_p else 1
            in_full = 0 if rnd.random() < .05 else 1
            sales.append(dict(OrderID=f"SO{so:07d}", OrderDate=d.isoformat(),
                              RequestedDate=(d + timedelta(7)).isoformat(),
                              ShipDate=(d + timedelta(7 + (0 if on_time else rnd.randint(1, 9)))).isoformat(),
                              CustomerID=rnd.choice(custs)["CustomerID"], ItemID=it["ItemID"], Qty=qty,
                              ShippedQty=qty if in_full else round(qty * rnd.uniform(.6, .95)),
                              ForecastQty=round(qty * rnd.uniform(.8, 1.35)),
                              NetValue=round(qty * it["UnitCost"] * 1.35, 2),
                              ShippedOnTime=on_time, ShippedInFull=in_full))

    # --- weekly inventory snapshots (C items drift into excess)
    inv, on_hand = [], {it["ItemID"]: it["_base"] * it["TargetCoverDays"] for it in items}
    prod, cap = [], []
    po = 0
    for d in days:
        if d.weekday() != 0:
            continue
        for it in items:
            drift = {"A": rnd.uniform(.85, 1.1), "B": rnd.uniform(.9, 1.15), "C": rnd.uniform(.97, 1.08)}[it["ABC"]]
            on_hand[it["ItemID"]] *= drift
            q = round(on_hand[it["ItemID"]])
            inv.append(dict(SnapshotDate=d.isoformat(), ItemID=it["ItemID"], OnHandQty=q,
                            StockValue=round(q * it["UnitCost"], 2)))
            po += 1
            planned = round(it["_base"] * 5 * rnd.uniform(.8, 1.2))
            adh = rnd.random() > (.3 if it["PrimaryWorkCenter"] == bottleneck else .1)
            prod.append(dict(ProdOrderID=f"PO{po:07d}", WeekStart=d.isoformat(), ItemID=it["ItemID"],
                             WorkCenterID=it["PrimaryWorkCenter"], PlannedQty=planned,
                             ConfirmedQty=planned if adh else round(planned * rnd.uniform(.5, .9)),
                             OnSchedule=int(adh)))
        for wc in wcs:
            wc_items = items if wc["WorkCenterID"] == "WC08" else [
                it for it in items if it["PrimaryWorkCenter"] == wc["WorkCenterID"]]
            hrs = 0.3 if wc["WorkCenterID"] == "WC08" else None
            season = 1 + 0.25 * math.sin(2 * math.pi * (d.timetuple().tm_yday - 60) / 365)
            req = sum(it["_base"] * 5 * (hrs or it["HoursPer1000"]) / 1000 * 10 for it in wc_items)
            cap.append(dict(WeekStart=d.isoformat(), WorkCenterID=wc["WorkCenterID"],
                            RequiredHours=round(req * season * rnd.uniform(.9, 1.1), 1), _wc=wc))

    # available hours sized so most work centres run 70-92%; WC07 is the bottleneck (~110%+ in peak)
    target = {w["WorkCenterID"]: rnd.uniform(.70, .92) for w in wcs}
    target[bottleneck] = 1.02
    for wc in wcs:
        rows = [r for r in cap if r["WorkCenterID"] == wc["WorkCenterID"]]
        avail = sum(r["RequiredHours"] for r in rows) / len(rows) / target[wc["WorkCenterID"]]
        for r in rows:
            r["AvailableHours"] = round(avail, 1)
            r.pop("_wc")

    for it in items:
        it.pop("_base")
    write("DimItem", items)
    write("DimWorkCenter", wcs)
    write("DimCustomer", custs)
    write("FactSales", sales)
    write("FactInventory", inv)
    write("FactProduction", prod)
    write("FactCapacity", cap)
    print(f"\nSaved to {OUT}. Build DimDate in Power BI with CALENDARAUTO().")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    main(ap.parse_args().seed)
