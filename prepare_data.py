"""Rebuild the two trimmed input files from the original downloads.
Usage: python prepare_data.py <folder with the original 01 .csv and 04 .xlsx>"""
import sys, re, csv, zipfile
import pandas as pd
from lxml import etree
src = sys.argv[1] if len(sys.argv) > 1 else "raw"

# 01: keep the rows and columns analysis.py uses
cols = ["dol_vehicle_id", "new_or_used_vehicle", "transaction_type", "state_of_residence", "date_of_vehicle_sale",
        "census_tract_2020", "make", "model", "electric_vehicle_type", "sale_price"]
r = pd.read_csv(f"{src}/01_WA_DOL_new_EV_registrations.csv", usecols=cols, low_memory=False)
r = r[(r.new_or_used_vehicle == "New") & (r.transaction_type == "Original Title") & (r.state_of_residence == "WA")]
d = pd.to_datetime(r.date_of_vehicle_sale, errors="coerce")
r[(d >= "2022-01-01") & (d <= "2025-06-30")].to_csv("data/01_WA_DOL_new_EV_registrations_trimmed.csv.gz", index=False, compression="gzip")

# 04: keep Washington counties (state FIPS 53); the workbook is read as XML because it is too large for pandas
z = zipfile.ZipFile(f"{src}/04_NREL_home_charging_access_by_county.xlsx")
ss = re.findall(r"<t[^>]*>([^<]*)</t>", z.read("xl/sharedStrings.xml").decode())
ns = "{http://purl.oclc.org/ooxml/spreadsheetml/main}"; rows = []
with z.open("xl/worksheets/sheet3.xml") as f:
    for _, el in etree.iterparse(f, tag=ns + "row"):
        v = {re.match(r"[A-Z]+", c.get("r")).group(): (ss[int(c.find(ns + "v").text)] if c.get("t") == "s" else c.find(ns + "v").text)
             for c in el if c.find(ns + "v") is not None}
        if v.get("B") == "53": rows.append([v["A"], v["C"], v["D"], v["E"], v["F"]])
        el.clear()
        while el.getprevious() is not None: del el.getparent()[0]
with open("data/04_NREL_home_charging_access_WA_counties.csv", "w", newline="") as g:
    w = csv.writer(g); w.writerow(["county_fips", "county_name", "scenario", "ev_share_of_stock", "home_charging_access"]); w.writerows(rows)
print("done")
