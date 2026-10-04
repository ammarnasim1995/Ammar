"""
Client data-readiness profiler (Delivery SOP step 2).

Reads every CSV/XLSX in a client's `02 Data In` folder and writes a markdown
data-quality report: row counts, date ranges, null %, duplicate keys,
negative quantities and orphan item codes versus the item master.

Usage:  python profile_data.py "<path to 02 Data In>" [--item-master DimItem]
Requires: pandas, openpyxl
"""
import argparse
from pathlib import Path

import pandas as pd

KEY_HINTS = ("id", "order", "item", "material", "sku")
QTY_HINTS = ("qty", "quantity", "stock", "onhand")


def load(folder: Path):
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() == ".csv":
            yield p.stem, pd.read_csv(p, low_memory=False)
        elif p.suffix.lower() in (".xlsx", ".xls"):
            for sheet, df in pd.read_excel(p, sheet_name=None).items():
                yield f"{p.stem}:{sheet}", df


def profile(name, df, items):
    out = [f"## {name}", f"- Rows: **{len(df):,}** · Columns: {df.shape[1]}"]
    for c in df.columns:
        if "date" in c.lower():
            d = pd.to_datetime(df[c], errors="coerce")
            out.append(f"- `{c}` range: {d.min():%Y-%m-%d} → {d.max():%Y-%m-%d} · unparseable: {d.isna().sum():,}")
    nulls = (df.isna().mean() * 100).round(1)
    bad = nulls[nulls > 0]
    out.append("- Null %: " + (", ".join(f"`{k}` {v}%" for k, v in bad.items()) if len(bad) else "none"))
    first = df.columns[0]
    if any(h in first.lower() for h in KEY_HINTS):
        out.append(f"- Duplicate `{first}`: {df[first].duplicated().sum():,}")
    for c in df.columns:
        if any(h in c.lower() for h in QTY_HINTS) and pd.api.types.is_numeric_dtype(df[c]):
            n = (df[c] < 0).sum()
            if n:
                out.append(f"- ⚠️ Negative `{c}`: {n:,} rows")
    if items is not None:
        col = next((c for c in df.columns if c.lower() in ("itemid", "item", "material", "sku")), None)
        if col:
            orphans = set(df[col].dropna()) - items
            out.append(f"- Orphan item codes vs item master: **{len(orphans):,}**")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--item-master", default="DimItem")
    a = ap.parse_args()
    folder = Path(a.folder)
    tables = dict(load(folder))
    im = next((df for n, df in tables.items() if n.split(":")[0] == a.item_master), None)
    items = set(im.iloc[:, 0]) if im is not None else None
    report = ["# Data Readiness Report", f"Source: `{folder}`", ""]
    report += [profile(n, df, items if n.split(":")[0] != a.item_master else None) for n, df in tables.items()]
    (folder / "data_readiness_report.md").write_text("\n\n".join(report))
    print("\n\n".join(report))


if __name__ == "__main__":
    main()
