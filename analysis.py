"""
Opening the Gates: Whose sales change, and where, when a firm shares its proprietary complement with rivals.
ESMA 722 Technology Strategy, Assignment III (Khalifa University, Fall 2026).

Builds the Washington State datasets (Section 3.2), the tract measures (Section 3.3), and estimates the
models for H1a-H3b with the robustness checks (Section 3.4). Run:  python analysis.py
Input files are read from data/ (see data/README.md); results are written to output/.
"""
import os, json, re, zipfile, time, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
D = os.environ.get("DATA_DIR", "data"); O = os.environ.get("OUT_DIR", "output"); os.makedirs(O, exist_ok=True)
t0 = time.time(); out = []
def P(*a):
    s = " ".join(map(str, a)); print(s, flush=True); out.append(s)
def pc(b): return 100 * (np.exp(b) - 1)
FE = dict(lean=True, store_data=False, fixef_tol=1e-6, fixef_maxiter=100000)
def est(formula, data, cluster="county"):
    return pf.fepois(formula, data=data, vcov={"CRV1": cluster}, **FE)
def get(m, term):
    r = m.tidy().loc[term]; return float(r["Estimate"]), float(r["Std. Error"]), float(r["Pr(>|t|)"])
RES = {}
def rep(label, m, term):
    b, s, p = get(m, term); RES[label] = (b, s, p); P(f"  {label:48s} {b:+.4f} ({s:.4f}) p={p:.3f}  {pc(b):+.1f}%")

# ---------------------------------------------------------------- 3.2 data and sample
P("# 3.2 Data and sample")
reg = pd.read_csv(f"{D}/01_WA_DOL_new_EV_registrations.csv", low_memory=False)
reg = reg[(reg.new_or_used_vehicle == "New") & (reg.transaction_type == "Original Title") & (reg.state_of_residence == "WA")].copy()
reg["sold"] = pd.to_datetime(reg.date_of_vehicle_sale, errors="coerce")
reg = reg[(reg.sold >= "2022-01-01") & (reg.sold <= "2025-06-30")]
reg = reg.drop_duplicates(subset="dol_vehicle_id").dropna(subset=["census_tract_2020"])
reg["tract"] = reg.census_tract_2020.astype("int64").astype(str).str.zfill(11)
reg = reg[reg.tract.str[:2] == "53"].copy()
reg["m"] = reg.sold.values.astype("datetime64[M]")
reg["make"] = reg.make.str.upper().str.strip(); reg["model"] = reg.model.astype(str).str.upper()
reg["type"] = np.select([reg.electric_vehicle_type.str.startswith("Battery"), reg.electric_vehicle_type.str.startswith("Plug")], ["BEV", "PHEV"], "other")
P(f"  new WA registrations in window: {len(reg):,}; BEV {int((reg.type=='BEV').sum()):,}; PHEV {int((reg.type=='PHEV').sum()):,}")

# brand units (Table 1): one unit per carmaker; Nissan and Lucid split by model; < 50 cars dropped; no access date -> outside units
wb = pd.ExcelFile(f"{D}/08_access_dates_by_manufacturer.xlsx")
dates = wb.parse("Access dates").iloc[:, :4]; dates.columns = ["unit", "makes", "announced", "access"]
dates = dates.dropna(subset=["access"]); dates["announced"] = pd.to_datetime(dates.announced); dates["access"] = pd.to_datetime(dates.access)
lk = wb.parse("Brand lookup").iloc[:, :2].dropna(); lk.columns = ["make", "unit"]; lk["make"] = lk.make.str.upper().str.strip()
m2u = {m: u for m, u in zip(lk.make, lk.unit) if u in set(dates.unit) or u == "Nissan"}
def unit(make, model):
    if make == "TESLA": return "Tesla"
    if make == "NISSAN": return "Nissan (Ariya)" if "ARIYA" in model else "Nissan (Leaf)"
    if make == "LUCID": return "Lucid (Gravity)" if "GRAVITY" in model else "Lucid (Air)"
    return m2u.get(make)
reg["unit"] = [unit(a, b) for a, b in zip(reg.make, reg.model)]
nxt = lambda d: pd.NaT if pd.isna(d) else (d if d.day == 1 else d + pd.offsets.MonthBegin(1)).normalize()
U = {r.unit: dict(access=r.access, announced=r.announced) for r in dates.itertuples()}
U["Nissan (Ariya)"] = U.pop("Nissan"); U["Nissan (Leaf)"] = dict(access=pd.NaT, announced=pd.NaT)
units = pd.DataFrame([dict(unit=k, access=v["access"], announced=v["announced"], access_m=nxt(v["access"]), ann_m=nxt(v["announced"])) for k, v in U.items()])
bev = reg[reg.type == "BEV"]
units["n"] = units.unit.map(bev.unit.value_counts()).fillna(0).astype(int)
units = units[units.n >= 50].copy()
units["role"] = np.where(units.access_m <= pd.Timestamp("2025-06-30"), "gains access", np.where(units.access_m.isna(), "never", "comparison"))
rivals = units.unit.tolist()
P(f"  rival units {len(rivals)} ({(units.role=='gains access').sum()} gain access, {(units.role=='comparison').sum()} comparison, {(units.role=='never').sum()} never); BEVs outside units {int(bev.unit.isna().sum() + (~bev.unit.isin(rivals+['Tesla']) & bev.unit.notna()).sum()):,}")

# ---------------------------------------------------------------- 3.3 tract measures (fixed before the opening)
P("# 3.3 Measures")
gz = pd.read_csv(f"{D}/09_Census_gazetteer_2022_WA_tract_coordinates.txt", sep="\t"); gz.columns = [c.strip() for c in gz.columns]
T = pd.DataFrame({"tract": gz.GEOID.astype(str).str.zfill(11), "lat": gz.INTPTLAT, "lon": gz.INTPTLONG, "sqmi": gz.ALAND_SQMI})
def miles(lat1, lon1, lat2, lon2):
    a, b, c, d = map(np.radians, (lat1, lon1, lat2, lon2))
    return 7917.6 * np.arcsin(np.sqrt(np.sin((c - a) / 2) ** 2 + np.cos(a) * np.cos(c) * np.sin((d - b) / 2) ** 2))
def sum_within_25(lat, lon, val):
    dm = miles(T.lat.values[:, None], T.lon.values[:, None], np.asarray(lat)[None, :], np.asarray(lon)[None, :])
    return (dm <= 25) @ np.asarray(val, float)
af = pd.read_csv(f"{D}/02_AFDC_charging_stations_US_2023-12-31.csv", low_memory=False)
af = af[af.State.isin(["WA", "OR", "ID"]) & (af["Access Code"] == "public") & (af["EV DC Fast Count"].fillna(0) > 0)]
af = af[pd.to_datetime(af["Open Date"], errors="coerce").fillna(pd.Timestamp("2000-01-01")) <= "2023-12-31"]
oth = af[af["EV Network"] != "Tesla"]
sc = pd.DataFrame([dict(lat=s["gps"]["latitude"], lon=s["gps"]["longitude"], st=s["address"].get("state"), status=s.get("status"),
                        opened=pd.to_datetime(s.get("dateOpened"), errors="coerce"), v34=(s.get("stalls") or {}).get("v3", 0) + (s.get("stalls") or {}).get("v4", 0))
                   for s in json.load(open(f"{D}/03_supercharge_info_Tesla_sites.json")) if s["address"].get("country") == "USA"])
sc = sc[sc.st.isin(["WA", "OR", "ID"]) & (sc.status == "OPEN") & (sc.opened <= "2023-12-31")]
T["other"] = sum_within_25(oth.Latitude, oth.Longitude, oth["EV DC Fast Count"])
T["v34"] = sum_within_25(sc.lat, sc.lon, sc.v34)
T["CommAlt"] = T.other / (T.other + T.v34).replace(0, np.nan)        # share of usable fast charging not owned by Tesla
T["TeslaStalls"] = np.log1p(T.v34)
T["Density"] = np.log1p(1 / T.sqmi.clip(lower=0.01))
hc = pd.read_csv(f"{D}/05_ACS_2022_5yr_B25032_housing_tenure_WA_tracts/ACSDT5Y2022.B25032-Data.csv", skiprows=[1], low_memory=False)
hc = hc.assign(tract=hc.GEO_ID.str[-11:], HomeCharge=lambda d: (pd.to_numeric(d.B25032_003E, errors="coerce") + pd.to_numeric(d.B25032_004E, errors="coerce")) / pd.to_numeric(d.B25032_001E, errors="coerce").replace(0, np.nan))
inc = pd.read_csv(f"{D}/06_ACS_2022_5yr_B19013_median_income_WA_tracts/ACSDT5Y2022.B19013-Data.csv", skiprows=[1], low_memory=False)
inc = inc.assign(tract=inc.GEO_ID.str[-11:], Income=lambda d: pd.to_numeric(d.B19013_001E.astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce"))
T = T.merge(hc[["tract", "HomeCharge"]], on="tract", how="left").merge(inc[["tract", "Income"]], on="tract", how="left")
T["county"] = T.tract.str[:5]
for c in ("HomeCharge", "Income"):
    T[c] = T[c].fillna(T.groupby("county")[c].transform("median"))
v = pd.read_csv(f"{D}/07_MIT_county_presidential_returns_2000-2024.csv", low_memory=False)
v = v[(v.state_po == "WA") & (v.year == 2020) & (v["mode"] == "TOTAL")]
share = (v[v.party == "DEMOCRAT"].groupby("county_fips").candidatevotes.sum() / v.groupby("county_fips").totalvotes.first())
T["VoteShare"] = T.county.map({str(int(k)).zfill(5): x for k, x in share.items()})
# estimation sample: tracts with a BEV and with usable fast charging within 25 miles
T = T[T.tract.isin(bev.tract.unique()) & (T.other + T.v34 > 0)].copy()
for c in ("CommAlt", "HomeCharge", "Income", "Density", "VoteShare"):
    T[c + "_z"] = (T[c] - T[c].mean()) / T[c].std()
P(f"  tracts in estimation {len(T):,}; CommAlt mean {T.CommAlt.mean():.3f} sd {T.CommAlt.std():.3f}; HomeCharge mean {T.HomeCharge.mean():.3f} sd {T.HomeCharge.std():.3f}")
months = pd.date_range("2022-01-01", "2025-06-01", freq="MS")

# ---------------------------------------------------------------- datasets
def rival_dataset(cars):
    c = cars[cars.unit.isin(rivals) & cars.tract.isin(T.tract)]
    y = c.groupby(["unit", "tract", "m"]).size()
    full = pd.MultiIndex.from_product([rivals, T.tract, months], names=["unit", "tract", "m"])
    d = y.reindex(full, fill_value=0).rename("y").reset_index()
    pm = cars[cars.unit.isin(rivals)].assign(p=lambda x: x.sale_price.where(x.sale_price >= 5000)).groupby(["unit", "m"]).agg(SalePrice=("p", "mean"), Models=("model", "nunique")).reset_index()
    d = d.merge(pm, on=["unit", "m"], how="left")
    d[["SalePrice", "Models"]] = d.groupby("unit")[["SalePrice", "Models"]].transform(lambda s: s.ffill().bfill())
    d["SalePrice"] = np.log(d.SalePrice)
    d = d.merge(units[["unit", "access_m", "ann_m", "role"]], on="unit").merge(T, on="tract")
    d["Access"] = (d.m >= d.access_m).fillna(False).astype(int); d["Announced"] = (d.m >= d.ann_m).fillna(False).astype(int)
    d["rel"] = ((d.m.dt.year - d.access_m.dt.year) * 12 + (d.m.dt.month - d.access_m.dt.month)).where(d.access_m.notna())
    d["bt"] = d.unit + "#" + d.tract; d["tm"] = d.tract + "#" + d.m.astype(str); d["cm"] = d.county + "#" + d.m.astype(str); d["bm"] = d.unit + "#" + d.m.astype(str)
    return d
R = rival_dataset(bev)
Y = bev[bev.tract.isin(T.tract)].groupby(["tract", "m"]).size().rename("Total")
Yt = bev[(bev.unit == "Tesla") & bev.tract.isin(T.tract)].groupby(["tract", "m"]).size().rename("Tesla")
Wn = pd.concat([Y, Yt], axis=1).reindex(pd.MultiIndex.from_product([T.tract, months], names=["tract", "m"]), fill_value=0).fillna(0).reset_index().merge(T, on="tract")
acc = units.access_m.dropna().sort_values(); ann = units.ann_m.dropna().sort_values()
Wn["N"] = Wn.m.map(lambda x: int((acc <= x).sum())); Wn["Nann"] = Wn.m.map(lambda x: int((ann <= x).sum()))
Wn["NonTesla"] = Wn.Total - Wn.Tesla; Wn["cm"] = Wn.county + "#" + Wn.m.astype(str)
PH = rival_dataset(reg[reg.type == "PHEV"]); PH = PH[PH.unit.isin(PH.groupby("unit").y.sum().loc[lambda s: s >= 50].index)]
P(f"  rival rows {len(R):,} (zero share {(R.y==0).mean():.3f}); owner rows {len(Wn):,}; N range {Wn.N.min()}-{Wn.N.max()}")

# ---------------------------------------------------------------- 3.4 estimation
CTRL = "Access:Income_z + Access:Density_z + Access:VoteShare_z"
P("# Baseline (reported, not hypothesised)")
rep("Baseline: Access, Eq.(1)", est("y ~ Access + SalePrice + Models | bt + tm", R), "Access")
P("# Eq.(1): H1a and H2a")
rep("H1a Eq.(1): Access x CommAlt", est(f"y ~ Access + Access:CommAlt_z + Access:TeslaStalls + {CTRL} + SalePrice + Models | bt + tm", R), "Access:CommAlt_z")
rep("H1a stricter: Access x CommAlt", est(f"y ~ Access:CommAlt_z + Access:TeslaStalls + {CTRL} | bt + cm + bm", R), "Access:CommAlt_z")
rep("H2a Eq.(1): Access x HomeCharge", est(f"y ~ Access + Access:HomeCharge_z + {CTRL} + SalePrice + Models | bt + tm", R), "Access:HomeCharge_z")
mB = est(f"y ~ Access:HomeCharge_z + {CTRL} | bt + cm + bm", R); rep("H2a stricter: Access x HomeCharge", mB, "Access:HomeCharge_z")
rep("H2a stricter, brand clusters", est(f"y ~ Access:HomeCharge_z + {CTRL} | bt + cm + bm", R, "unit"), "Access:HomeCharge_z")
P("# Eq.(2): H1b, H2b, then Total for H3a, H3b")
X2 = "N:CommAlt_z + N:TeslaStalls + N:HomeCharge_z + N:Income_z + N:Density_z"
mo = est(f"Tesla ~ {X2} | tract + cm", Wn); rep("H1b Eq.(2): N x CommAlt (predicted +)", mo, "N:CommAlt_z"); rep("H2b Eq.(2): N x HomeCharge (predicted -)", mo, "N:HomeCharge_z")
mt = est(f"Total ~ {X2} | tract + cm", Wn); rep("H3a Total: N x CommAlt (predicted -)", mt, "N:CommAlt_z"); rep("H3b Total: N x HomeCharge (predicted 0)", mt, "N:HomeCharge_z")
mn = est(f"NonTesla ~ {X2} | tract + cm", Wn); rep("decomposition: NonTesla x CommAlt", mn, "N:CommAlt_z"); rep("decomposition: NonTesla x HomeCharge", mn, "N:HomeCharge_z")
b, s, p = RES["H3b Total: N x HomeCharge (predicted 0)"]; P(f"  H3b with nine rivals: {pc(9*b):+.1f}%, 90% CI [{pc(9*(b-1.645*s)):+.1f}%, {pc(9*(b+1.645*s)):+.1f}%]")
b, s, p = RES["H3a Total: N x CommAlt (predicted -)"]; P(f"  H3a with nine rivals, one SD fewer alternatives: {pc(-9*b):+.1f}%")
P("# Checks promised in 3.4: event study, announcement dates, plug-in hybrids; clustering")
rep("H2b Tesla, tract clusters", est(f"Tesla ~ {X2} | tract + cm", Wn, "tract"), "N:HomeCharge_z")
rep("H3a Total, tract clusters", est(f"Total ~ {X2} | tract + cm", Wn, "tract"), "N:CommAlt_z")
ma = est("Tesla ~ Nann:CommAlt_z + N:CommAlt_z + Nann:HomeCharge_z + N:HomeCharge_z + Nann:Income_z + N:Income_z + Nann:Density_z + N:Density_z + N:TeslaStalls | tract + cm", Wn)
rep("H2b announcement vs access: access term", ma, "N:HomeCharge_z"); rep("H2b announcement vs access: announced term", ma, "Nann:HomeCharge_z")
ma = est("Total ~ Nann:CommAlt_z + N:CommAlt_z + Nann:HomeCharge_z + N:HomeCharge_z + Nann:Income_z + N:Income_z + Nann:Density_z + N:Density_z + N:TeslaStalls | tract + cm", Wn)
rep("H3a announcement vs access: access term", ma, "N:CommAlt_z"); rep("H3a announcement vs access: announced term", ma, "Nann:CommAlt_z")
ma = est(f"y ~ Announced:HomeCharge_z + Access:HomeCharge_z + Announced:Income_z + Access:Income_z + Announced:Density_z + Access:Density_z + Announced:VoteShare_z + Access:VoteShare_z | bt + cm + bm", R)
rep("H2a announcement vs access: access term", ma, "Access:HomeCharge_z"); rep("H2a announcement vs access: announced term", ma, "Announced:HomeCharge_z")
rep("H2a PHEV placebo (Eq.1 with county-month FE)", est(f"y ~ Access + Access:HomeCharge_z + {CTRL} | bt + cm", PH), "Access:HomeCharge_z")
ph = PH.groupby(["tract", "m"]).y.sum().rename("PHEV"); W2 = Wn.merge(ph, left_on=["tract", "m"], right_index=True, how="left").fillna({"PHEV": 0})
mp = est("PHEV ~ N:CommAlt_z + N:HomeCharge_z + N:Income_z + N:Density_z | tract + cm", W2)
rep("H2b PHEV placebo outcome: N x HomeCharge", mp, "N:HomeCharge_z"); rep("H3a PHEV placebo outcome: N x CommAlt", mp, "N:CommAlt_z")
# event studies (quarterly, reference 2023Q4 = last quarter before any access) for the owner-side gradients
Wn["q"] = Wn.m.dt.to_period("Q").astype(str)
for ycol, var, lab in [("Tesla", "HomeCharge_z", "H2b"), ("Total", "HomeCharge_z", "H3b"), ("Total", "CommAlt_z", "H3a")]:
    other = "CommAlt_z" if var == "HomeCharge_z" else "HomeCharge_z"
    me = est(f"{ycol} ~ i(q, {var}, ref='2023Q4') + i(q, {other}, ref='2023Q4') + i(q, Income_z, ref='2023Q4') + i(q, Density_z, ref='2023Q4') | tract + cm", Wn)
    tt = me.tidy(); tt = tt[tt.index.str.contains(var)].copy(); tt["q"] = tt.index.str.extract(r"q::(\d{4}Q\d)")[0].values
    pre = tt[tt.q < "2024Q1"].Estimate; post = tt[tt.q >= "2024Q4"].Estimate
    P(f"  {lab} event study ({ycol} x {var}) vs 2023Q4: pre-2024 mean {pre.mean():+.3f}, from 2024Q4 mean {post.mean():+.3f}, shift {post.mean()-pre.mean():+.3f}")
    tt.to_csv(f"{O}/event_{lab}.csv")
# rival-side event study for the home-charging interaction, relative to the pre-access average
E = R.copy(); E["post"] = ((E.rel >= 0) & (E.role == "gains access")).astype(int); E["pre_slope"] = np.where((E.role == "gains access") & (E.rel < 0), E.rel.clip(-24, 0), 0)
me = est("y ~ post + post:HomeCharge_z + pre_slope:HomeCharge_z + post:Income_z + post:Density_z + post:VoteShare_z + SalePrice + Models | bt + tm", E)
rep("H2a post vs pre-average (pre-trend slope allowed)", me, "post:HomeCharge_z"); rep("   pre-access slope x HomeCharge", me, "pre_slope:HomeCharge_z")

# ---------------------------------------------------------------- verdicts
P("# Verdicts")
def v(k): return RES[k]
rows = []
b, s, p = v("Baseline: Access, Eq.(1)"); rows.append(("Baseline", f"{pc(b):+.1f}% (p={p:.2f})", "reported"))
bA, _, pA = v("H1a Eq.(1): Access x CommAlt"); bB, _, pB = v("H1a stricter: Access x CommAlt"); rows.append(("H1a", f"{pc(bA):+.1f}% (p={pA:.2f}); stricter {pc(bB):+.1f}% (p={pB:.2f})", "Yes" if bA < 0 and pA < .05 and bB < 0 and pB < .05 else "No"))
b, _, p = v("H1b Eq.(2): N x CommAlt (predicted +)"); rows.append(("H1b", f"{pc(b):+.1f}%/brand (p={p:.2f})", "Yes" if b > 0 and p < .05 else "No"))
bA, _, pA = v("H2a Eq.(1): Access x HomeCharge"); bB, _, pB = v("H2a stricter: Access x HomeCharge"); rows.append(("H2a", f"{pc(bA):+.1f}% (p={pA:.3f}); stricter {pc(bB):+.1f}% (p={pB:.3f})", "Yes" if bA > 0 and pA < .05 and bB > 0 and pB < .05 else ("Weak" if bA > 0 and pA < .05 and bB > 0 and pB < .10 else "No")))
b, _, p = v("H2b Eq.(2): N x HomeCharge (predicted -)"); rows.append(("H2b", f"{pc(b):+.1f}%/brand (p={p:.3f})", "Yes" if b < 0 and p < .05 else "No"))
b, _, p = v("H3a Total: N x CommAlt (predicted -)"); rows.append(("H3a", f"{pc(b):+.1f}%/brand (p={p:.3f}); see event study", "Yes (point estimate)" if b < 0 and p < .05 else "No"))
b, s, p = v("H3b Total: N x HomeCharge (predicted 0)"); rows.append(("H3b", f"{pc(b):+.1f}%/brand (p={p:.2f}); 90% CI 9 brands [{pc(9*(b-1.645*s)):+.1f}%, {pc(9*(b+1.645*s)):+.1f}%]", "Yes (redistribution)" if not (b > 0 and p < .05) else "No"))
V = pd.DataFrame(rows, columns=["H", "estimate", "verdict"]); P(V.to_string(index=False)); V.to_csv(f"{O}/verdicts.csv", index=False)
pd.DataFrame([dict(test=k, b=b, se=s, p=p, pct=pc(b)) for k, (b, s, p) in RES.items()]).to_csv(f"{O}/results.csv", index=False)
open(f"{O}/log.txt", "w").write("\n".join(out)); P(f"DONE {(time.time()-t0)/60:.1f} min")
