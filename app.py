# PRISM AI — Executive Decision Intelligence | ONE Google Colab cell
# Beyond the numbers. Into the decisions.
import subprocess, sys, os, re, zipfile, html, math, warnings
warnings.filterwarnings("ignore")
try:
    import gradio, plotly, sklearn, scipy
    assert int(gradio.__version__.split(".")[0]) in (4, 5)
except Exception:
    subprocess.call([sys.executable, "-m", "pip", "install", "-q", "gradio>=4.44,<6", "plotly", "scikit-learn>=1.2", "scipy", "pandas", "numpy", "requests"])
import numpy as np, pandas as pd, plotly.graph_objects as go, gradio as gr, requests
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, IsolationForest

C = dict(mid="#202C36", sl="#344650", sg="#B8E3C7", go="#D7B878", iv="#F3F2EC", li="#C9B8F0", co="#E58C83", st="#AAB9C0")
G = {}; TESTS = []; _D = {}
BL = ["", "nan", "none", "n/a", "na", "-", "null", "nat"]
esc = lambda x: html.escape(str(x)); nul = lambda v: v is None or (not isinstance(v, str) and bool(pd.isna(v)))
nf = lambda v, d=0: "—" if nul(v) else format(v, ",." + str(d) + "f"); fx = lambda v, d=1: "—" if nul(v) else format(v, "." + str(d) + "f")
pc = lambda v, d=0: "—" if nul(v) else format(v, "." + str(d) + "%"); sg = lambda v: "—" if nul(v) else "%+.1f%%" % (100 * v); mon = lambda v: "—" if nul(v) else pd.Timestamp(v).strftime("%b %Y")
def fv(v, u):
    if nul(v): return "—"
    if u == "₹k": return "₹" + nf(v) + "k"
    if u == "%": return fx(v, 1) + "%"
    if u in ("₹", "visits", "count"): return ("₹" if u == "₹" else "") + nf(v)
    return fx(v, 2 if abs(v) < 10 else 1) + ("" if u in ("index", "x", "") else " " + u)
FVC = {"Favourable": ("✓", C["sg"]), "Unfavourable": ("▲", C["co"]), "On track": ("●", C["st"])}
def pill(s, col=None): g, c = FVC.get(s, ("", C["st"])); return "<span class='pill' style='background:%s'>%s %s</span>" % (col or c, g, esc(s))
def note(t, k="info"): return "<div class='note' style='border-left:4px solid %s'>%s</div>" % ({"info": C["st"], "ok": C["sg"], "warn": C["go"], "err": C["co"], "ai": C["li"]}[k], t)
def card(l, v, d, c=C["mid"]): return "<div class='kc'><div class='kl'>%s</div><div class='kv' style='color:%s'>%s</div><div class='kd'>%s</div></div>" % (l, c, v, d)
SEC = lambda t: "<div class='sec'>%s</div>" % t
def tbl(d, cols, fmt=None):
    fmt = fmt or {}; h = "<div class='tw'><table><tr>" + "".join("<th>%s</th>" % n for _, n in cols) + "</tr>"
    for _, r in d.iterrows(): h += "<tr>" + "".join("<td>%s</td>" % (fmt[k](r[k]) if k in fmt else ("—" if nul(r[k]) else esc(r[k]))) for k, _n in cols) + "</tr>"
    return h + "</table></div>"
def sty(f, h=340, t=""):
    f.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=C["mid"]), height=h, title=dict(text=t, x=.02), margin=dict(l=55, r=25, t=50, b=45), legend=dict(orientation="h", y=-.25), colorway=[C["mid"], C["go"], C["li"], C["co"], C["st"]]); return f
def empty(m):
    f = go.Figure(); f.add_annotation(text=m, showarrow=False, font=dict(color=C["st"], size=14)); f.update_xaxes(visible=False); f.update_yaxes(visible=False); return sty(f, 280)
def banner(): return note("<b>Illustrative synthetic data.</b> Fictional company with planted relationships; not a real business and not a discovery about one.", "warn") if G.get("demo") else ""
def safe(n):
    def deco(fn):
        def w(*a):
            def out(m): return m if n == 1 else (m,) + (None,) * (n - 1)
            if "D" not in G: return out(note("Load data first."))
            try: return fn(*a)
            except Exception as e: return out(note("Could not render this page: " + esc(e), "err"))
        return w
    return deco
nm_ = lambda s: re.sub(r"\W+", "_", str(s).strip().lower()).strip("_")
def clean_str(s): t = s.astype(str).str.strip(); return t.where(~(s.isna() | t.str.lower().isin(BL)), np.nan)
def to_num(s): return s.astype(float) if pd.api.types.is_numeric_dtype(s) else pd.to_numeric(s.astype(str).str.replace(r"[₹$,%\s]", "", regex=True), errors="coerce")
def to_dt(s):
    if pd.api.types.is_datetime64_any_dtype(s): return s
    try: return pd.to_datetime(s, errors="coerce", format="mixed")
    except Exception: return pd.to_datetime(s, errors="coerce")
def read_csv_any(f):
    p = f if isinstance(f, str) else getattr(f, "name", f)
    try: d = pd.read_csv(p)
    except Exception: d = pd.read_csv(p, sep=None, engine="python", encoding_errors="replace")
    if d.empty: raise ValueError("A file contains no rows.")
    return d

# ------------------------------ KPI registry and FICTIONAL synthetic enterprise (fixed seed) ------------------------------
KS = """revenue|Revenue|Finance|Finance|₹k|sum|up|Σ segment revenue|CFO
cogs|Cost of goods sold|Finance|Finance|₹k|sum|down|Σ direct costs|CFO
gross_profit|Gross profit|Finance|Finance|₹k|sum|up|revenue − COGS|CFO
opex|Operating expenses|Finance|Finance|₹k|sum|down|Σ operating costs|CFO
operating_profit|Operating profit|Finance|Finance|₹k|sum|up|gross profit − opex|CFO
website_traffic|Website visits|Sales & Marketing|Marketing|visits|sum|up|Σ monthly sessions|CMO
conversion_rate|Conversion rate|Sales & Marketing|Sales|%|mean|up|orders ÷ visits × 100|Head of Sales
aov|Average order value|Sales & Marketing|Sales|₹|mean|up|revenue ÷ orders|Head of Sales
win_rate|Win rate|Sales & Marketing|Sales|%|mean|up|deals won ÷ deals closed × 100|Head of Sales
new_customers|New customers|Sales & Marketing|Sales|count|sum|up|first-time buyers|Head of Sales
marketing_spend|Marketing spend|Sales & Marketing|Marketing|₹k|sum|neutral|Σ campaign cost|CMO
cac|Customer acquisition cost|Sales & Marketing|Marketing|₹|mean|down|marketing spend ÷ new customers|CMO
email_ctr|Email click-through rate|Sales & Marketing|Marketing|%|mean|up|clicks ÷ delivered × 100|CMO
brand_awareness|Brand awareness|Sales & Marketing|Marketing|%|mean|up|survey recall|CMO
otd_rate|On-time delivery rate|Operations|Operations|%|mean|up|on-time ÷ delivered × 100|COO
defect_rate|Defect rate|Operations|Operations|%|mean|down|defective ÷ produced × 100|COO
order_cycle_time|Order cycle time|Operations|Operations|days|mean|down|order → delivery|COO
inventory_turnover|Inventory turnover|Operations|Operations|x|mean|up|COGS ÷ average inventory|COO
capacity_util|Capacity utilisation|Operations|Operations|%|mean|neutral|used ÷ available capacity × 100|COO
nps|Net promoter score|Customer Experience|Customer|index|mean|up|%promoters − %detractors|CX Head
csat|Customer satisfaction|Customer Experience|Customer|%|mean|up|satisfied ÷ responses × 100|CX Head
complaint_rate|Complaint rate|Customer Experience|Customer|per 1000 orders|mean|down|complaints ÷ orders × 1000|CX Head
first_response_h|First response time|Customer Experience|Customer|hours|mean|down|median first reply|CX Head
retention_rate|Customer retention rate|Customer Experience|Customer|%|mean|up|retained ÷ starting customers × 100|CX Head
supplier_otd|Supplier on-time rate|Supply Chain|Supply chain|%|mean|up|on-time receipts ÷ receipts × 100|CPO
lead_time_days|Supplier lead time|Supply Chain|Supply chain|days|mean|down|order → receipt|CPO
stockout_rate|Stock-out rate|Supply Chain|Supply chain|%|mean|down|SKU-days out of stock ÷ SKU-days × 100|CPO
freight_cost_pct|Freight cost share|Supply Chain|Supply chain|%|mean|down|freight ÷ revenue × 100|CPO
attrition_rate|Attrition rate|HR|HR|%|mean|down|leavers ÷ average headcount × 100|CHRO
absenteeism|Absenteeism|HR|HR|%|mean|down|absent days ÷ scheduled days × 100|CHRO
overtime_hours|Overtime per FTE|HR|HR|hours|mean|down|overtime hours ÷ FTE|CHRO
headcount|Headcount|HR|HR|count|sum|neutral|active employees|CHRO
training_hours|Training hours per FTE|HR|HR|hours|mean|up|training hours ÷ FTE|CHRO
enps|Employee NPS|HR|HR|index|mean|up|%promoters − %detractors (employees)|CHRO"""
KD = pd.DataFrame([l.split("|") for l in KS.split("\n")], columns=["kpi_id", "name", "department", "category", "unit", "aggregation", "direction", "formula", "owner"]); KD["frequency"] = "monthly"; KD["source"] = "synthetic"
DER = {"gross_margin_pct": ("Gross margin", "gross_profit ÷ revenue × 100", "gross_profit"), "operating_margin_pct": ("Operating margin", "operating_profit ÷ revenue × 100", "operating_profit")}
KDD = pd.concat([KD, pd.DataFrame([dict(kpi_id=k, name=n, department="Finance", category="Finance", unit="%", aggregation="derived", direction="up", formula=f, owner="CFO", frequency="monthly", source="derived") for k, (n, f, _b) in DER.items()])], ignore_index=True)
FIN = {"revenue", "cogs", "gross_profit", "opex", "operating_profit", "gross_margin_pct", "operating_margin_pct"}; OUTS = ("revenue", "gross_margin_pct", "operating_profit"); MECH = {o: {"website_traffic", "conversion_rate", "aov"} for o in ("revenue", "gross_profit", "operating_profit")}
FREE = dict(win_rate=(24, .05, .02, .03), new_customers=(420, .10, .1, .1), marketing_spend=(180, .08, .05, .1), cac=(820, .08, 0, 0), email_ctr=(2.8, .1, 0, .05), brand_awareness=(38, .03, .02, 0), defect_rate=(1.8, .15, -.05, 0), order_cycle_time=(3.4, .08, -.03, 0), inventory_turnover=(6.2, .07, .02, 0), capacity_util=(78, .04, 0, .05),
            csat=(86, .02, 0, 0), complaint_rate=(14, .15, -.03, 0), first_response_h=(5.5, .12, -.05, 0), supplier_otd=(91, .02, 0, 0), lead_time_days=(14, .08, 0, 0), stockout_rate=(3.2, .2, 0, 0), freight_cost_pct=(4.5, .08, 0, 0), attrition_rate=(14, .12, 0, 0), absenteeism=(3.1, .15, 0, .1),
            overtime_hours=(9, .2, 0, .1), headcount=(120, .01, .05, 0), training_hours=(4, .2, 0, 0), enps=(22, .3, 0, 0)); SUMK = {"new_customers", "marketing_spend", "headcount"}
PER = pd.date_range("2023-11-01", periods=36, freq="MS"); T = 36; REG = ["North", "South", "West"]
def make_data(seed=7):
    r = np.random.default_rng(seed); t = np.arange(T); sea = np.sin(2 * np.pi * (PER.month.values - 3) / 12); dirn = dict(zip(KD.kpi_id, KD.direction)); out = []
    for ri, g in enumerate(REG):
        sc = [1.0, .8, .65][ri]; z = lambda s=1.0: r.standard_normal(T) * s
        v = {k: b * (sc if k in SUMK else 1) * (1 + tr * t / 12) * (1 + sa * sea) * np.exp(sd * z()) for k, (b, sd, tr, sa) in FREE.items()}
        nps = 40 + 5 * np.sin(t / 6 + ri) + .1 * t + z(3.0); otd = np.clip(91 + 3 * np.sin(t / 5 + ri) + z(1.0), 70, 99.5); conv = 3.0 + .15 * sea + .004 * t + z(.1); aov = 62 * (1 + .02 * t / 12) * np.exp(.03 * z())
        if ri == 1: conv[-4:] *= .85
        if ri == 2: aov[-6:] *= 1.08
        traffic = 400000 * sc * (1 + .12 * t / 12) * (1 + .15 * sea) * np.exp(.04 * z()); v["retention_rate"] = np.clip(88 + .08 * (nps - 40) + z(.8), 70, 99); nl = np.r_[np.full(2, nps[0]), nps[:-2]]
        rev = traffic * conv / 100 * aov / 1000 * (1 + .012 * (nl - 40)); gm = .42 + .012 * (otd - 91) - .02 * (v["defect_rate"] - 1.8) + z(.006); gp = rev * gm; opex = (120 * sc + .12 * rev + 6 * sc * (v["overtime_hours"] - 9)) * np.exp(.02 * z())
        v.update(website_traffic=traffic, conversion_rate=conv, aov=aov, nps=nps, otd_rate=otd, revenue=rev, cogs=rev - gp, gross_profit=gp, opex=opex, operating_profit=gp - opex); bd = {}
        for k, a in v.items():
            if k in ("gross_profit", "operating_profit"): continue
            s = pd.Series(a); b = s.rolling(6, min_periods=1).mean().shift(1); b.iloc[0] = s.iloc[0]; bd[k] = b.values * (1 + {"up": .02, "down": -.02, "neutral": 0}[dirn[k]])
        bd["gross_profit"] = bd["revenue"] - bd["cogs"]; bd["operating_profit"] = bd["gross_profit"] - bd["opex"]
        for k in v: out.append(pd.DataFrame(dict(period=PER, segment=g, kpi_id=k, actual=v[k], budget=bd[k])))
    B = pd.concat(out, ignore_index=True); fb = ["revenue", "cogs", "gross_profit", "opex", "operating_profit"]; F = B[B.kpi_id.isin(fb)].pivot_table(index=["period", "segment"], columns="kpi_id", values="actual").reset_index()[["period", "segment"] + fb]
    return dict(fin=F, ops=B[~B.kpi_id.isin(fb)][["period", "segment", "kpi_id", "actual"]].rename(columns={"actual": "value"}), bud=B[["period", "segment", "kpi_id", "actual", "budget"]], dic=KDD.copy())
def demo_raw(seed=7):
    if ("r", seed) not in _D: _D[("r", seed)] = make_data(seed)
    return _D[("r", seed)]
def demo_D(seed=7):
    if ("d", seed) not in _D: _D[("d", seed)] = load_all(demo_raw(seed))
    return _D[("d", seed)]

# ------------------------------ ingestion, validation, reconciliation ------------------------------
SP = dict(dic=[("kpi_id", 1, ["id", "metric_id", "kpi"]), ("name", 1, ["kpi_name", "metric"]), ("department", 0, ["dept"]), ("category", 0, []), ("unit", 1, ["uom"]), ("aggregation", 0, ["agg"]), ("direction", 1, ["polarity", "good_direction"]), ("formula", 0, ["definition"]), ("frequency", 0, []), ("owner", 0, ["business_owner"]), ("source", 0, ["data_source"])],
          fin=[("period", 1, ["month", "date"]), ("segment", 0, ["region", "business_unit"])], ops=[("period", 1, ["month", "date"]), ("segment", 0, ["region", "business_unit"]), ("kpi_id", 1, ["kpi", "metric_id"]), ("value", 1, ["actual", "amount"])],
          bud=[("period", 1, ["month", "date"]), ("segment", 0, ["region", "business_unit"]), ("kpi_id", 1, ["kpi", "metric_id"]), ("actual", 0, ["value"]), ("budget", 1, ["plan", "target"])])
TN = dict(dic="kpi_dictionary", fin="financial_performance", ops="operational_kpis", bud="budget_actuals")
def parse_map(text):
    ov = {}
    for p in re.split(r"[,;\n]", text or ""):
        if "=" in p: k, v = p.split("=", 1); ov[nm_(k)] = nm_(v)
    return ov
def cmap(raw, t, ov, iss):
    d = raw.copy(); d.columns = [nm_(c) for c in d.columns]; ren = {}
    for f, req, al in SP[t]:
        c = ov.get(f); c = c if c in d.columns else next((a for a in [f] + [nm_(x) for x in al] if a in d.columns and a not in ren), None)
        if c is None or c in ren:
            if req: iss.append(("error", "%s: required field '%s' not found. Columns found: %s. Use the mapping box, e.g. %s=your_column." % (TN[t], f, ", ".join(map(str, raw.columns[:12])), f)))
            continue
        ren[c] = f
    d = d.rename(columns=ren); return d.loc[:, ~d.columns.duplicated()]
def load_all(raw, mapping=""):
    iss, ex, ov = [], [], parse_map(mapping)
    if raw.get("dic") is None: raise ValueError("Missing required table: kpi_dictionary.")
    if raw.get("fin") is None and raw.get("ops") is None: raise ValueError("Provide financial_performance and/or operational_kpis.")
    rows_in = {t: len(raw[t]) for t in TN if raw.get(t) is not None}; Tt = {t: cmap(raw[t], t, ov, iss) for t in rows_in}; errs = [m for l, m in iss if l == "error"]
    if errs: raise ValueError(" | ".join(errs))
    K = Tt["dic"].copy()
    for c in ("department", "category", "aggregation", "formula", "frequency", "owner", "source"):
        if c not in K: K[c] = np.nan
    K["kpi_id"] = clean_str(K["kpi_id"]); K = K[K.kpi_id.notna()]; dup = K.duplicated("kpi_id", keep="first")
    if dup.any(): iss.append(("warn", "kpi_dictionary: %d duplicate kpi_id rows ignored (first kept): %s" % (dup.sum(), ", ".join(K.kpi_id[dup].head(5))))); ex.append(("kpi_dictionary", "duplicate kpi_id", int(dup.sum()))); K = K[~dup]
    K["department"] = K.department.fillna("Unassigned"); K["category"] = K.category.fillna(K.department); K["unit"] = K.unit.fillna("").astype(str); K["aggregation"] = K["aggregation"].astype(str).str.lower().map(lambda a: a if a in ("sum", "mean", "derived") else np.nan)
    if K["aggregation"].isna().any(): iss.append(("info", "%d KPIs have no valid aggregation (sum / mean / derived): treated as mean across segments (assumption)." % K["aggregation"].isna().sum())); K["aggregation"] = K["aggregation"].fillna("mean")
    def dr(v):
        s = str(v).lower()
        if re.search(r"up|high|incr|\+|better", s) and not re.search(r"down|low|decr|worse", s): return "up"
        return "down" if re.search(r"down|low|decr", s) else "neutral"
    K["direction"] = K.direction.map(dr); dn = K[K.duplicated("name", keep=False)]
    if len(dn): iss.append(("warn", "kpi_dictionary: duplicate KPI definitions (same name, different ids): " + ", ".join(sorted(set(dn.name))[:5])))
    uu = K.groupby("name").unit.nunique()
    if (uu > 1).any(): iss.append(("warn", "kpi_dictionary: inconsistent units for: " + ", ".join(uu.index[uu > 1][:5])))
    def cl(d, name, numc):
        d = d.copy(); d["period"] = to_dt(d["period"]); d["kpi_id"] = clean_str(d["kpi_id"]); d["segment"] = clean_str(d["segment"]).fillna("Company") if "segment" in d else "Company"
        for c in numc: d[c] = to_num(d[c]) if c in d else np.nan
        d["_row"] = np.arange(len(d)) + 2; bad = pd.Series(False, index=d.index)
        for why, m in [("invalid or missing period", d.period.isna()), ("missing kpi_id", d.kpi_id.isna()), ("kpi_id not in kpi_dictionary", ~d.kpi_id.isin(K.kpi_id) & d.kpi_id.notna()), ("non-numeric or missing value", d[numc].isna().all(axis=1))]:
            m = m & ~bad
            if m.any(): ex.append((name, why, int(m.sum()))); iss.append(("warn", "%s: %d rows excluded: %s (rows %s)" % (name, m.sum(), why, ", ".join(str(i) for i in d["_row"][m].values[:6])))); bad = bad | m
        d = d[~bad]
        if len(d) and (d.period.dt.day != 1).mean() > .5: iss.append(("info", "%s: dates were normalised to month start (monthly grain)." % name))
        d["period"] = d.period.dt.to_period("M").dt.to_timestamp(); dp = d.duplicated(["period", "segment", "kpi_id"], keep="first")
        if dp.any(): ex.append((name, "duplicate period+segment+kpi_id", int(dp.sum()))); iss.append(("warn", "%s: %d duplicate period/segment/KPI rows ignored (first kept). Weekly or daily data must be aggregated before upload: grains are never mixed." % (name, dp.sum())))
        return d[~dp].drop(columns="_row").reset_index(drop=True)
    parts = []
    if "fin" in Tt:
        f = Tt["fin"].copy(); idc = [c for c in f.columns if c not in ("period", "segment")]; use = [c for c in idc if c in set(K.kpi_id)]; unk = [c for c in idc if c not in set(K.kpi_id)]
        if unk: iss.append(("warn", "financial_performance: columns not in kpi_dictionary were ignored: " + ", ".join(unk[:6])))
        if "segment" not in f: f["segment"] = "Company"
        parts.append(f.melt(id_vars=["period", "segment"], value_vars=use, var_name="kpi_id", value_name="actual"))
    if "ops" in Tt:
        o = Tt["ops"].copy()
        if "segment" not in o: o["segment"] = "Company"
        parts.append(o.rename(columns={"value": "actual"})[["period", "segment", "kpi_id", "actual"]])
    L = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["period", "segment", "kpi_id", "actual"]); L = cl(L, "actuals", ["actual"]) if len(L) else L; key = ["period", "segment", "kpi_id"]
    if "bud" in Tt:
        b = cl(Tt["bud"], "budget_actuals", ["actual", "budget"])
        if L.empty: L = b[key + ["actual"]].dropna(subset=["actual"]).copy()
        else:
            m = L.merge(b[key + ["actual"]].rename(columns={"actual": "a2"}), on=key, how="inner"); c = ((m.actual - m.a2).abs() > .01 * m.actual.abs() + 1e-9) & m.a2.notna()
            if c.any(): iss.append(("warn", "%d metric values in budget_actuals conflict with the actuals tables by more than 1%% (actuals tables were used)." % c.sum()))
        L = L.merge(b[key + ["budget"]], on=key, how="left")
    else: L["budget"] = np.nan
    if L.empty: raise ValueError("No valid KPI observations remain after validation.")
    for k, (n, f, base) in DER.items():
        if k not in set(K.kpi_id) and base in set(L.kpi_id) and "revenue" in set(L.kpi_id): K = pd.concat([K, pd.DataFrame([dict(kpi_id=k, name=n, department="Finance", category="Finance", unit="%", aggregation="derived", direction="up", formula=f, owner=np.nan, frequency="monthly", source="derived")])], ignore_index=True)
    allp = pd.date_range(L.period.min(), L.period.max(), freq="MS"); gaps = {}
    for (s, k), g in L.groupby(["segment", "kpi_id"]):
        m = len(allp) - g.period.nunique()
        if m > 0: gaps[k] = gaps.get(k, 0) + m
    if gaps: iss.append(("warn", "Missing periods (months with no value; never filled in): " + ", ".join("%s %d" % (k, v) for k, v in list(gaps.items())[:6])))
    for s, g in L.groupby("segment"):
        p = g.pivot_table(index="period", columns="kpi_id", values="actual", aggfunc="first")
        for need, lhs, rhs in ((("revenue", "cogs", "gross_profit"), "gross_profit", lambda p: p.revenue - p.cogs), (("gross_profit", "opex", "operating_profit"), "operating_profit", lambda p: p.gross_profit - p.opex)):
            if set(need) <= set(p.columns):
                e = ((p[lhs] - rhs(p)).abs() / p.get("revenue", p[lhs]).abs().replace(0, np.nan)) > .005
                if e.any(): iss.append(("warn", "Financial reconciliation failed for %s in %d months of segment %s (tolerance 0.5%% of revenue). Values were kept as supplied, not corrected." % (lhs.replace("_", " "), e.sum(), s)))
    if L.period.nunique() < 24: iss.append(("warn", "Only %d monthly periods: relationship, driver and anomaly results are unreliable (24+ recommended)." % L.period.nunique()))
    return dict(L=L, K=K.reset_index(drop=True), issues=iss, excluded=ex, rows_in=rows_in, segs=sorted(L.segment.unique()), pers=sorted(L.period.unique()))

# ------------------------------ core analytics ------------------------------
def derive(W):
    if {"gross_profit", "revenue"} <= set(W.columns): W["gross_margin_pct"] = 100 * W.gross_profit / W.revenue.replace(0, np.nan)
    if {"operating_profit", "revenue"} <= set(W.columns): W["operating_margin_pct"] = 100 * W.operating_profit / W.revenue.replace(0, np.nan)
    return W
def wide(L, K, seg="All", col="actual"):
    d = L if seg in (None, "All") else L[L.segment == seg]; am = dict(zip(K.kpi_id, K.aggregation)); d = d[["period", "kpi_id", col]].dropna(subset=[col])
    if d.empty: return pd.DataFrame()
    d = d.assign(a=d.kpi_id.map(am).fillna("mean")); d = d[d.a != "derived"]; s = d[d.a == "sum"].groupby(["period", "kpi_id"])[col].sum(); m = d[d.a != "sum"].groupby(["period", "kpi_id"])[col].mean()
    W = pd.concat([s, m]).unstack("kpi_id").sort_index(); W = W.reindex(pd.date_range(W.index.min(), W.index.max(), freq="MS")); return derive(W)
def ctx(D, seg, per):
    W = wide(D["L"], D["K"], seg); B = wide(D["L"], D["K"], seg, "budget"); W = W[W.index <= per]
    if len(B): B = B.reindex(W.index)
    return W, B
def favour(chg, dirn, thr):
    if nul(chg) or dirn == "neutral" or abs(chg) < thr: return "On track"
    return "Favourable" if (chg > 0) == (dirn == "up") else "Unfavourable"
ch_ = lambda a, b: np.nan if (nul(a) or nul(b) or b == 0) else (a - b) / abs(b)
def catalogue(D, W, B, thr):
    K = D["K"].set_index("kpi_id"); n = len(W); rows = []
    for k in W.columns:
        s = W[k]
        if s.notna().sum() == 0: continue
        cur = s.iloc[-1]; prev = s.iloc[-2] if n > 1 else np.nan; yo = s.iloc[-13] if n > 12 else np.nan; bud = B[k].iloc[-1] if (len(B) and k in B.columns) else np.nan
        dr = K.direction.get(k, "neutral") if k in K.index else "neutral"; vb = ch_(cur, bud); mom = ch_(cur, prev); z = s.dropna().tail(12); tr = "n/a"
        if len(z) >= 8: r_ = stats.linregress(np.arange(len(z)), z.values); tr = "rising" if (r_.pvalue < .05 and r_.slope > 0) else ("falling" if r_.pvalue < .05 else "flat")
        rho = np.nan
        if "revenue" in W and k not in FIN:
            m = pd.concat([s, W["revenue"]], axis=1).dropna()
            if len(m) >= 12 and m.iloc[:, 0].nunique() > 2: rho = stats.spearmanr(m.iloc[:, 0], m.iloc[:, 1])[0]
        g = lambda c, d_="": (K[c].get(k, d_) if k in K.index else d_)
        rows.append(dict(kpi_id=k, name=g("name", k), department=g("department", "Unassigned"), category=g("category", ""), unit=g("unit", ""), formula=g("formula", np.nan), owner=g("owner", np.nan), source=g("source", np.nan), direction=dr, cur=cur, prev=prev, mom=mom, yoy=ch_(cur, yo), bud=bud, vb=vb, status=favour(vb if not nul(vb) else mom, dr, thr), trend=tr, compl=s.notna().mean(), rho=rho))
    c = pd.DataFrame(rows); c["cur_s"] = [fv(a, u) for a, u in zip(c.cur, c.unit)]; c["bud_s"] = [fv(a, u) for a, u in zip(c.bud, c.unit)]; return c
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n); prev = 1.0
    for i in range(n - 1, -1, -1): j = o[i]; prev = min(prev, p[j] * n / (i + 1)); q[j] = prev
    return q
def strength(r, p, q, n):
    if nul(r): return "insufficient data"
    if q < .05 and abs(r) >= .3 and n >= 24: return "supported"
    return "tentative" if p < .05 else "not supported"
def rel_table(W, o, drv, lags, diff, min_n=12):
    y = W[o].diff() if diff else W[o]; rows = []
    for d in drv:
        x0 = W[d].diff() if diff else W[d]
        for L_ in lags:
            m = pd.concat([y, x0.shift(L_)], axis=1).dropna(); n = len(m); r = dict(driver=d, lag=L_, n=n, pearson=np.nan, spearman=np.nan, p=np.nan)
            if n >= min_n and m.iloc[:, 0].nunique() > 2 and m.iloc[:, 1].nunique() > 2: r["pearson"] = stats.pearsonr(m.iloc[:, 0], m.iloc[:, 1])[0]; sp = stats.spearmanr(m.iloc[:, 0], m.iloc[:, 1]); r["spearman"] = sp[0]; r["p"] = sp[1]
            rows.append(r)
    Tb = pd.DataFrame(rows, columns=["driver", "lag", "n", "pearson", "spearman", "p"]); Tb["q"] = np.nan; ok = Tb.p.notna()
    if ok.any(): Tb.loc[ok, "q"] = bh(Tb.p[ok].values)
    Tb["strength"] = [strength(a, b, c, d) for a, b, c, d in zip(Tb.spearman, Tb.p, Tb.q, Tb.n)]; Tb["mech"] = Tb.driver.isin(MECH.get(o, set())); return Tb
def anomalies(W, win, zthr=3.5):
    out = []; wset = set(W.index[-win:]); K = G["D"]["K"].set_index("kpi_id") if "D" in G else None
    for k in W.columns:
        s = W[k].dropna()
        if len(s) < 14: continue
        d = s.diff().dropna(); sc = 1.4826 * np.median(np.abs(d - np.median(d))) + 1e-9 * max(1.0, abs(s.mean())); base = s.rolling(6, min_periods=4).median().shift(1); z = (s - base) / sc
        for p_, zz in z.items():
            if p_ in wset and pd.notna(zz) and abs(zz) >= zthr: out.append(dict(kind="Jump vs recent median (robust z)", period=p_, kpi_id=k, value=s[p_], expected=base[p_], z=zz, why="Value %s vs recent 6-month median %s = %.1f robust σ of typical monthly moves; may be seasonal or a real event, not necessarily an error." % (nf(s[p_], 1), nf(base[p_], 1), zz)))
    X = W.loc[:, [c for c in W.columns if W[c].notna().sum() >= 24]]
    if X.shape[1] >= 5 and len(X) >= 24:
        md = X.median(); sc = (1.4826 * (X - md).abs().median()).replace(0, np.nan); Xz = ((X - md) / sc).fillna(0).clip(-8, 8); pr = IsolationForest(n_estimators=150, contamination=.04, random_state=0).fit_predict(Xz)
        for p_, f, row in zip(X.index, pr, Xz.values):
            if f == -1 and p_ in wset: top = pd.Series(row, index=X.columns).abs().sort_values(ascending=False).head(3); out.append(dict(kind="Unusual month across KPIs (Isolation Forest)", period=p_, kpi_id=", ".join(top.index), value=np.nan, expected=np.nan, z=float(top.iloc[0]), why="Combination of KPIs unlike other months; largest deviations: " + ", ".join("%s (%.1fσ)" % (a, b) for a, b in top.items())))
    return pd.DataFrame(out, columns=["kind", "period", "kpi_id", "value", "expected", "z", "why"])
def lmdi(y0, y1, pairs):
    Lw = (y1 - y0) / math.log(y1 / y0) if (abs(y1 - y0) > 1e-12 and y0 > 0 and y1 > 0) else max(y0, 0.0)
    return [Lw * math.log(b / a) if a > 0 and b > 0 else 0.0 for a, b in pairs]
def bridges(D, seg, per, n=3):
    L = D["L"]; ps = [p for p in D["pers"] if p <= per]; segs = D["segs"] if seg == "All" else [seg]; need = ["website_traffic", "conversion_rate", "aov", "revenue", "gross_profit", "opex", "operating_profit"]
    if len(ps) < 2 * n: return dict(err="needs at least %d months of history up to the selected period." % (2 * n))
    if not set(need) <= set(L.kpi_id): return dict(err="needs revenue, gross_profit, opex, operating_profit, website_traffic, conversion_rate and aov in the data.")
    cur, prv = ps[-n:], ps[-2 * n:-n]
    def agg(g, months, k, how):
        x = L[(L.segment == g) & (L.kpi_id == k) & L.period.isin(months)].actual
        return (x.sum() if how == "sum" else x.mean()) if len(x) == len(months) else np.nan
    rows = dict(website_traffic=0.0, conversion_rate=0.0, aov=0.0); S = dict(f0=0.0, f1=0.0, R0=0.0, R1=0.0, G0=0.0, G1=0.0, X0=0.0, X1=0.0, P0=0.0, P1=0.0)
    for g in segs:
        v = {}
        for tag, mo in (("0", prv), ("1", cur)): v[tag] = dict(T=agg(g, mo, "website_traffic", "sum"), C=agg(g, mo, "conversion_rate", "mean"), A=agg(g, mo, "aov", "mean"), R=agg(g, mo, "revenue", "sum"), GP=agg(g, mo, "gross_profit", "sum"), OX=agg(g, mo, "opex", "sum"), OP=agg(g, mo, "operating_profit", "sum"))
        if any(nul(x) for d in v.values() for x in d.values()): return dict(err="months are missing for segment %s in the comparison windows." % g)
        a, b = v["0"], v["1"]; f0 = a["T"] * a["C"] / 100 * a["A"] / 1000; f1 = b["T"] * b["C"] / 100 * b["A"] / 1000
        for k_, x in zip(rows, lmdi(f0, f1, [(a["T"], b["T"]), (a["C"], b["C"]), (a["A"], b["A"])])): rows[k_] += x
        for k_, x in (("f0", f0), ("f1", f1), ("R0", a["R"]), ("R1", b["R"]), ("G0", a["GP"]), ("G1", b["GP"]), ("X0", a["OX"]), ("X1", b["OX"]), ("P0", a["OP"]), ("P1", b["OP"])): S[k_] += x
    gm0, gm1 = S["G0"] / S["R0"], S["G1"] / S["R1"]; vol = (S["R1"] - S["R0"]) * gm0; rate = S["R1"] * (gm1 - gm0); opx = -(S["X1"] - S["X0"])
    return dict(err=None, cur=cur, prv=prv, rows=rows, dRf=S["f1"] - S["f0"], dR=S["R1"] - S["R0"], resid=(S["R1"] - S["R0"]) - (S["f1"] - S["f0"]), S=S, gm0=gm0, gm1=gm1, vol=vol, rate=rate, opx=opx, total=vol + rate + opx, dOP=S["P1"] - S["P0"])

# ------------------------------ driver model (chronological, leakage-safe) ------------------------------
def driver_model(D, o, drv, per, win, k=5, test_frac=.3):
    pan = []
    for g in D["segs"]:
        W = wide(D["L"], D["K"], g)
        if o not in W: continue
        W = W[W.index <= per].tail(win); F = pd.DataFrame(index=W.index); F["y"] = W[o]; F["y_prev"] = W[o].shift(1)
        for d in drv:
            if d in W: F["x_" + d] = W[d]; F["l1_" + d] = W[d].shift(1)
        F["seg"] = g; pan.append(F)
    if not pan: return dict(ok=False, why="the outcome is not available.")
    P = pd.concat(pan).dropna(subset=["y"]); pers = sorted(P.index.unique())
    if len(pers) < 18: return dict(ok=False, why="needs at least 18 monthly periods (found %d): descriptive and correlation analysis only." % len(pers))
    cut = pers[int(round(len(pers) * (1 - test_frac)))]; tr = np.asarray(P.index < cut); te = ~tr; cols = [c for c in P.columns if c != "seg"]; Z = P.copy(); segv = P.seg.values
    for g in np.unique(segv):
        m = segv == g; mt = m & tr
        if mt.sum() < 6: continue
        mu = P.loc[mt, cols].mean(); sd = P.loc[mt, cols].std(ddof=0).replace(0, np.nan); Z.loc[m, cols] = ((P.loc[m, cols] - mu) / sd).values
    def pick(pre):
        sc = {}
        for d in drv:
            c = pre + d
            if c in Z:
                m = Z.loc[tr, ["y", c]].dropna()
                if len(m) >= 20 and m[c].nunique() > 2: sc[d] = abs(stats.spearmanr(m["y"], m[c])[0])
        return [d for d, _ in sorted(sc.items(), key=lambda t_: -t_[1])[:k]]
    s1, s0 = pick("l1_"), pick("x_")
    if not s1 or not s0: return dict(ok=False, why="no usable drivers in the training period.")
    f1 = ["y_prev"] + ["l1_" + d for d in s1]; Zn = Z[f1 + ["y"]].astype(float); use = Zn.notna().all(axis=1).values; trm, tem = tr & use, te & use
    if trm.sum() < 30 or tem.sum() < 10: return dict(ok=False, why="too few complete rows for a chronological train/test evaluation (%d train, %d test)." % (trm.sum(), tem.sum()))
    Xv, yv = Zn[f1].values, Zn["y"].values; pred = dict(Naive=Z["y_prev"].values[tem], Ridge=Ridge(alpha=5.0).fit(Xv[trm], yv[trm]).predict(Xv[tem]), RandomForest=RandomForestRegressor(n_estimators=200, max_depth=3, min_samples_leaf=4, random_state=0).fit(Xv[trm], yv[trm]).predict(Xv[tem]))
    mae = lambda p: float(np.mean(np.abs(yv[tem] - p))); rm = lambda p: float(np.sqrt(np.mean((yv[tem] - p) ** 2))); mn = mae(pred["Naive"])
    perf = pd.DataFrame([dict(model={"Naive": "Naive: previous month", "Ridge": "Ridge: lagged drivers + previous month", "RandomForest": "Random forest: same features"}[k_], mae=mae(p), rmse=rm(p), skill=1 - mae(p) / mn) for k_, p in pred.items()])
    f0 = ["x_" + d for d in s0]; Z0 = Z[f0 + ["y"]].astype(float).dropna(); Zx = Z0[f0].values; yy = Z0["y"].values; A = np.c_[np.ones(len(yy)), Zx]; beta = np.linalg.lstsq(A, yy, rcond=None)[0]; res = yy - A @ beta; s2 = res @ res / max(len(yy) - A.shape[1], 1); se = np.sqrt(np.diag(s2 * np.linalg.pinv(A.T @ A))); vif = []
    for j in range(Zx.shape[1]):
        ot = np.c_[np.ones(len(Zx)), np.delete(Zx, j, 1)]; b = np.linalg.lstsq(ot, Zx[:, j], rcond=None)[0]; r2 = 1 - ((Zx[:, j] - ot @ b) ** 2).sum() / max(((Zx[:, j] - Zx[:, j].mean()) ** 2).sum(), 1e-12); vif.append(1 / max(1 - r2, 1e-6))
    coef = pd.DataFrame(dict(driver=s0, beta=beta[1:], se=se[1:], lo=beta[1:] - 1.96 * se[1:], hi=beta[1:] + 1.96 * se[1:], vif=vif)); coef["mech"] = coef.driver.isin(MECH.get(o, set()))
    rf = RandomForestRegressor(n_estimators=200, max_depth=3, min_samples_leaf=4, random_state=0).fit(Xv[trm], yv[trm]); imp = pd.DataFrame(dict(feature=f1, importance=rf.feature_importances_)).sort_values("importance", ascending=False)
    pdf = pd.DataFrame(dict(period=P.index[tem], seg=segv[tem], y=yv[tem], **{k_: v for k_, v in pred.items()})); err = pdf.assign(e=(pdf.y - pdf.Ridge).abs()); byseg = err.groupby("seg").e.mean().reset_index(); top = err.sort_values("e", ascending=False).head(5)
    return dict(ok=True, split=(P.index[tr].max(), P.index[te].min()), n_tr=int(trm.sum()), n_te=int(tem.sum()), perf=perf, coef=coef, imp=imp, pred=pdf, byseg=byseg, top=top, s1=s1, s0=s0, train_mean=float(np.nanmean(Z.loc[tr, "y"])), test_mean=float(np.nanmean(Z.loc[te, "y"])))

# ------------------------------ decisions and scenarios ------------------------------
DEFW = dict(impact=.30, urgency=.20, evidence=.20, effort=.10, feas=.10, risk=.10); TYP = dict(variance=(.5, .6, .3), bridge=(.5, .6, .3), assoc=(.6, .5, .3), anomaly=(.2, .9, .1))
def make_actions(D, R):
    cat = R["cat"].set_index("kpi_id"); K = D["K"].set_index("kpi_id"); thr = R["thr"]; A = []; own = lambda k: (K.owner.get(k) if (k in K.index and not nul(K.owner.get(k))) else "Not supplied")
    def add(t, prob, k, act, imp, basis, ev, evs, urg): A.append(dict(type=t, problem=prob, kpi=k, action=act, impact_k=imp, basis=basis, evidence=ev, evid_s=evs, urg_s=float(np.clip(urg, 0, 1)), owner=own(k)))
    for k in ("revenue", "gross_profit", "operating_profit", "opex"):
        if k in cat.index and not nul(cat.vb[k]) and cat.status[k] == "Unfavourable": add("variance", "%s is %s %s budget in %s" % (cat.name[k], pc(abs(cat.vb[k]), 1), "below" if cat.vb[k] < 0 else "above", mon(R["per"])), k, "Review the drivers of the %s gap and agree a recovery plan or a re-forecast" % cat.name[k].lower(), abs(cat.cur[k] - cat.bud[k]), "measured actual − budget, latest month", "measured (arithmetic)", .9, abs(cat.vb[k]) / (5 * thr))
    br = R["br"]
    if br.get("err") is None:
        for k, v in sorted(br["rows"].items(), key=lambda t_: t_[1])[:2]:
            if v < 0: add("bridge", "%s reduced revenue by ₹%sk (last 3 months vs prior 3)" % (cat.name[k] if k in cat.index else k, nf(abs(v))), k, "Investigate and address the decline in %s" % (cat.name[k].lower() if k in cat.index else k), abs(v), "formula bridge: revenue = traffic × conversion × AOV", "formula-based decomposition", .8, abs(v) / max(abs(br["dR"]), 1e-9))
    for o, Tb in R["rel"].items():
        for r in Tb[(Tb.strength == "supported") & ~Tb.mech].assign(a=lambda d: d.spearman.abs()).sort_values("a", ascending=False).head(3).itertuples():
            if r.driver in cat.index and cat.status[r.driver] == "Unfavourable": add("assoc", "%s is unfavourable and statistically associated with %s (rho %+.2f, lag %d)" % (cat.name[r.driver], o.replace("_", " "), r.spearman, r.lag), r.driver, "Investigate %s: confirm the mechanism before investing (association, not proven cause)" % cat.name[r.driver].lower(), np.nan, "no monetary estimate (association only)", "statistical association (q<0.05)", .6, .4 + .2 * abs(r.spearman))
    an = R["an"]
    if len(an):
        for r in an[an.period >= R["per"] - pd.DateOffset(months=1)].head(2).itertuples(): add("anomaly", "Unusual movement flagged in %s (%s)" % (r.kpi_id, mon(r.period)), r.kpi_id.split(",")[0], "Validate the data point and check for a one-off event before acting", np.nan, "no monetary estimate", "anomaly flag (unvalidated)", .4, .6)
    A = pd.DataFrame(A, columns=["type", "problem", "kpi", "action", "impact_k", "basis", "evidence", "evid_s", "urg_s", "owner"]).head(12)
    if A.empty: return A
    mx = A.impact_k.max(); A["impact_s"] = [min(1, v / mx) if (not nul(v) and mx > 0) else .3 for v in A.impact_k]; A["effort"] = [TYP[t_][0] for t_ in A.type]; A["feas"] = [TYP[t_][1] for t_ in A.type]; A["risk"] = [TYP[t_][2] for t_ in A.type]; A.insert(0, "id", ["A%02d" % (i + 1) for i in range(len(A))]); return A
def score_actions(A, w):
    if A.empty: return A
    s = sum(w.values()) or 1.0; A = A.copy(); A["score"] = 100 * (w["impact"] * A.impact_s + w["urgency"] * A.urg_s + w["evidence"] * A.evid_s + w["effort"] * (1 - A.effort) + w["feas"] * A.feas + w["risk"] * (1 - A.risk)) / s
    A = A.sort_values("score", ascending=False).reset_index(drop=True); A["rank"] = np.arange(1, len(A) + 1); return A
def scen_calc(b, lev, f, v):
    r1 = b["R"] * (1 + lev["t"] * f / 100) * (1 + lev["c"] * f / 100) * (1 + lev["a"] * f / 100); gp = r1 * (b["GP"] / b["R"] + lev["g"] * f / 100); ox = b["OX"] * ((1 - v) + v * r1 / b["R"]) * (1 + lev["o"] * f / 100)
    return dict(rev=r1, gp=gp, gm=100 * gp / r1, ox=ox, op=gp - ox, om=100 * (gp - ox) / r1)

# ------------------------------ analysis pipeline and narrative ------------------------------
def analyze(D, seg, per, win, thr):
    per = pd.Timestamp(per + "-01") if (isinstance(per, str) and len(per) == 7) else pd.Timestamp(per); W, B = ctx(D, seg, per)
    if len(W) < 3: raise ValueError("Fewer than 3 periods up to the selected month.")
    R = dict(W=W, B=B, per=per, seg=seg, win=win, thr=thr, n=len(W)); R["cat"] = catalogue(D, W, B, thr); Ww = W.tail(win); drv = [c for c in Ww.columns if c not in FIN and Ww[c].notna().sum() >= 12]; R["drivers"] = drv
    R["rel"] = {o: rel_table(Ww, o, drv, range(4), True) for o in OUTS if o in Ww}; R["an"] = anomalies(W, win); R["br"] = bridges(D, seg, per); R["act"] = make_actions(D, R); return R
def getR(seg, per, win, thr):
    k = (seg, str(per), int(win), float(thr), G["ver"])
    if k not in G["_c"]: G["_c"][k] = analyze(G["D"], seg, per, int(win), float(thr) / 100)
    return G["_c"][k]
def narrative(R):
    cat = R["cat"].set_index("kpi_id"); g = lambda k, c: cat[c].get(k, np.nan) if k in cat.index else np.nan; u = lambda k: cat.unit.get(k, "") if k in cat.index else ""; per = mon(R["per"]); out = []
    out.append(("1. What changed?", "In %s revenue was %s (%s vs prior month, %s vs budget, %s year on year); gross margin %s (%s vs budget); operating profit %s (%s vs budget). %s" % (per, fv(g("revenue", "cur"), "₹k"), sg(g("revenue", "mom")), sg(g("revenue", "vb")), sg(g("revenue", "yoy")), fv(g("gross_margin_pct", "cur"), "%"), sg(g("gross_margin_pct", "vb")), fv(g("operating_profit", "cur"), "₹k"), sg(g("operating_profit", "vb")),
                 ("Largest unfavourable operational moves: " + ", ".join("%s %s" % (r.name, sg(r.mom)) for r in cat[(cat.status == "Unfavourable") & ~cat.index.isin(FIN)].assign(a=lambda d: d.mom.abs()).sort_values("a", ascending=False).head(3).itertuples()) + ".") if ((cat.status == "Unfavourable") & ~cat.index.isin(FIN)).any() else "No operational KPI moved materially against its target.")))
    br = R["br"]
    if br.get("err"): out.append(("2. Why does it matter financially?", "The financial bridge is unavailable: " + br["err"]))
    else:
        rr = br["rows"]; out.append(("2. Why does it matter financially?", "Between the prior 3 months (%s–%s) and the latest 3 (%s–%s) revenue changed by ₹%sk. By the formula revenue = traffic × conversion × AOV, traffic contributed ₹%sk, conversion ₹%sk and AOV ₹%sk; ₹%sk is not explained by that formula (other effects). Operating profit changed by ₹%sk: volume ₹%sk, gross-margin rate ₹%sk, operating expenses ₹%sk." % (mon(br["prv"][0]), mon(br["prv"][-1]), mon(br["cur"][0]), mon(br["cur"][-1]), nf(br["dR"]), nf(rr["website_traffic"]), nf(rr["conversion_rate"]), nf(rr["aov"]), nf(br["resid"]), nf(br["dOP"]), nf(br["vol"]), nf(br["rate"]), nf(br["opx"]))))
    sp = [(o, r) for o, Tb in R["rel"].items() for r in Tb[Tb.strength == "supported"].assign(a=lambda d: d.spearman.abs()).sort_values("a", ascending=False).head(3).itertuples()]
    out.append(("3. Which indicators are associated?", ("Supported after multiple-testing control (q<0.05, month-to-month changes): " + "; ".join("%s ↔ %s (lag %d, rho %+.2f, n=%d, q=%.3f%s)" % (o.replace("_", " "), cat.name.get(r.driver, r.driver), r.lag, r.spearman, r.n, r.q, ", arithmetic link" if r.mech else "") for o, r in sp) + ". These are associations, not causes.") if sp else "No relationship passed the multiple-testing screen (q<0.05): treat any pattern as tentative."))
    A = score_actions(R["act"], DEFW); out.append(("4. What action should management consider?", ("; ".join("#%d %s: %s (owner: %s)" % (r.rank, r.problem, r.action, r.owner) for r in A.head(3).itertuples()) + ". Priority scores are a ranking aid, not a probability of success.") if len(A) else "No evidence-supported action was generated for this period."))
    out.append(("5. What evidence and limitations support this?", "Based on %d monthly periods for %s with %d KPIs. %d data-quality warnings. Relationships are statistical associations on month-to-month changes; confounders (seasonality, price, promotions, mix) are not controlled. Bridges use stated formulas; scenarios are hypothetical.%s" % (R["n"], R["seg"], len(R["cat"]), sum(1 for l, _ in G["D"]["issues"] if l == "warn"), " Data are synthetic." if G.get("demo") else "")))
    return out

# ------------------------------ pages ------------------------------
def wf(vals, labels, title, tot="Total"):
    f = go.Figure(go.Waterfall(x=labels + [tot], measure=["relative"] * len(vals) + ["total"], y=list(vals) + [0], increasing=dict(marker=dict(color=C["sg"])), decreasing=dict(marker=dict(color=C["co"])), totals=dict(marker=dict(color=C["mid"])), connector=dict(line=dict(color=C["st"])))); return sty(f, 340, title)
@safe(3)
def render_brief(seg, per, win, thr):
    R = getR(seg, per, win, thr); G["f"] = (seg, per, win, thr); cat = R["cat"].set_index("kpi_id"); W, B = R["W"], R["B"]
    def kc(k, lab):
        if k not in cat.index: return ""
        r = cat.loc[k]; return card(lab, fv(r.cur, r.unit), "vs budget %s · MoM %s · YoY %s %s" % (sg(r.vb), sg(r.mom), sg(r.yoy), {"Favourable": "✓", "Unfavourable": "▲", "On track": "●"}[r.status]), {"Favourable": C["mid"], "Unfavourable": C["co"], "On track": C["mid"]}[r.status])
    h = banner() + "<div class='kg'>" + kc("revenue", "Revenue") + kc("gross_margin_pct", "Gross margin") + kc("opex", "Operating expenses") + kc("operating_profit", "Operating profit") + kc("operating_margin_pct", "Operating margin") + "</div>"
    h += note("<b>Actuals</b> are measured; <b>budget</b> comes from the budget table; briefing statements are generated from the numbers below, and <b>associations</b> are labelled as such. Direction-aware: a rise in a 'lower is better' KPI is unfavourable.", "info")
    for t_, x in narrative(R): h += "<div class='note' style='border-left:4px solid %s'><b>%s</b><br>%s</div>" % (C["go"], t_, esc(x))
    mv = cat[~cat.index.isin(FIN) & (cat.status != "On track")].assign(a=lambda d: d.mom.abs()).sort_values("a", ascending=False).head(12); h += SEC("Material KPI movements (vs budget where available, otherwise vs prior month)") + (tbl(mv, [("name", "KPI"), ("department", "Department"), ("cur_s", "Actual"), ("bud_s", "Budget"), ("mom", "MoM"), ("vb", "vs budget"), ("status", "Status")], dict(mom=sg, vb=sg, status=pill)) if len(mv) else note("No operational KPI is outside the materiality threshold.", "ok"))
    Ww = W.tail(win); f1 = go.Figure()
    for k, c in (("revenue", C["mid"]), ("operating_profit", C["go"])):
        if k in Ww: f1.add_trace(go.Scatter(x=Ww.index, y=Ww[k], name=cat.name.get(k, k) + " (actual)", line=dict(color=c, width=3)))
        if len(B) and k in B: f1.add_trace(go.Scatter(x=Ww.index, y=B[k].reindex(Ww.index), name=cat.name.get(k, k) + " (budget)", line=dict(color=c, dash="dot")))
    f1 = sty(f1, 340, "Revenue and operating profit: actual vs budget (₹k)"); f2 = go.Figure(go.Bar(y=mv.name, x=mv.mom * 100, orientation="h", marker_color=[FVC[s][1] for s in mv.status])) if len(mv) else empty("No material movements"); f2 = sty(f2, 340, "Month-on-month change of material KPIs (%)"); return h, f1, f2
@safe(3)
def render_kpi(seg, per, win, thr, dept, q, st, cmpk, det):
    R = getR(seg, per, win, thr); c = R["cat"]; W, B = R["W"], R["B"]
    if dept and dept != "All": c = c[c.department == dept]
    if q: c = c[c.name.str.contains(q, case=False) | c.kpi_id.str.contains(q, case=False) | c.formula.fillna("").str.contains(q, case=False)]
    if st and st != "All": c = c[c.status == st]
    dq = [m for l, m in G["D"]["issues"] if m.startswith("kpi_dictionary") or m.startswith("Missing periods") or "conflict" in m]
    h = banner() + note("%d of %d KPIs shown. <b>Status</b> compares the latest value with budget (or the prior month if no budget) against the %s materiality threshold, using each KPI's own direction. <b>Assoc. with revenue</b> is a Spearman rho on levels (trend-inflated; see Relationship Explorer for the controlled analysis)." % (len(c), len(R["cat"]), pc(R["thr"], 0)), "info") + "".join(note(esc(m), "warn") for m in dq)
    h += tbl(c, [("name", "KPI"), ("department", "Department"), ("unit", "Unit"), ("formula", "Formula"), ("cur_s", "Actual"), ("bud_s", "Budget"), ("vb", "vs budget"), ("mom", "MoM"), ("yoy", "YoY"), ("status", "Status"), ("trend", "12-mo trend"), ("compl", "Completeness"), ("rho", "Assoc. with revenue"), ("owner", "Owner"), ("source", "Source")], dict(vb=sg, mom=sg, yoy=sg, status=pill, compl=pc, rho=lambda v: fx(v, 2)))
    f1 = empty("Select KPIs to compare"); f2 = empty("Select a KPI for detail")
    if cmpk:
        f1 = go.Figure()
        for k in cmpk:
            if k in W: s = W[k].dropna(); f1.add_trace(go.Scatter(x=s.index, y=s / s.iloc[0] * 100, name=k))
        f1 = sty(f1, 340, "Selected KPIs indexed to 100 at their first observation")
    if det and det in W:
        u = R["cat"].set_index("kpi_id").unit.get(det, ""); f2 = go.Figure([go.Scatter(x=W.index, y=W[det], name="Actual", line=dict(color=C["mid"], width=3))] + ([go.Scatter(x=W.index, y=B[det], name="Budget", line=dict(color=C["go"], dash="dot"))] if len(B) and det in B else [])); f2 = sty(f2, 340, "%s (%s)" % (det, u))
        d = G["D"]["L"]; d = d[(d.kpi_id == det) & (d.period == R["per"])]; h += SEC("Latest value by segment: " + esc(det)) + (tbl(d[["segment", "actual", "budget"]], [("segment", "Segment"), ("actual", "Actual"), ("budget", "Budget")], dict(actual=lambda v: fx(v, 2), budget=lambda v: fx(v, 2))) if len(d) else "")
    return h, f1, f2
@safe(4)
def render_rel(seg, per, win, thr, o, drv, ml, diff, sel, sl):
    R = getR(seg, per, win, thr); Ww = R["W"].tail(win); o = o or "revenue"; dd = [d for d in (drv or []) if d in Ww.columns] or R["drivers"]; Tb = rel_table(Ww, o, dd, range(int(ml) + 1), bool(diff)); ok = Tb[Tb.p.notna()]
    h = banner() + note("<b>Outcome:</b> %s. Observations are monthly and aligned by date for <b>%s</b> only (grains are never mixed). A lag of L months pairs the outcome with the driver L months earlier. %d tests were run: p-values are corrected with Benjamini–Hochberg (q). %s <b>Correlation is not causation:</b> seasonality, price, promotions and mix are uncontrolled confounders, and trending series inflate correlations." % (o.replace("_", " "), esc(seg), len(ok), "Month-to-month changes are used, which removes shared trends." if diff else "<b>Levels are used: trending series can correlate by coincidence. Prefer the changes option.</b>"), "info")
    tp = ok.assign(a=ok.spearman.abs()).sort_values("a", ascending=False).head(25); h += tbl(tp, [("driver", "Driver KPI"), ("lag", "Lag (mo)"), ("n", "n"), ("pearson", "Pearson"), ("spearman", "Spearman"), ("p", "p"), ("q", "q (FDR)"), ("strength", "Evidence"), ("mech", "Arithmetic link")], dict(pearson=lambda v: fx(v, 2), spearman=lambda v: fx(v, 2), p=lambda v: fx(v, 4), q=lambda v: fx(v, 4), mech=lambda v: "yes: revenue = traffic × conversion × AOV" if v else ""))
    t5 = tp.driver.drop_duplicates().head(8).tolist()
    if len(t5) > 1: cm = Ww[t5].diff().corr() if diff else Ww[t5].corr(); pr = [(a, b, cm.loc[a, b]) for i, a in enumerate(t5) for b in t5[i + 1:] if abs(cm.loc[a, b]) > .85]; h += note("Redundancy / multicollinearity among top drivers (|r| > 0.85): " + ("; ".join("%s ~ %s (%.2f)" % p for p in pr) if pr else "none.") + " Redundant KPIs should not be read as independent evidence.", "warn" if pr else "info")
    hm = ok.pivot_table(index="driver", columns="lag", values="spearman"); top = hm.abs().max(axis=1).sort_values(ascending=False).head(15).index; f1 = go.Figure(go.Heatmap(z=hm.loc[top].values, x=["lag %d" % c for c in hm.columns], y=list(top), zmin=-1, zmax=1, colorscale=[[0, C["co"]], [.5, "#ffffff"], [1, C["mid"]]], hovertemplate="%{y} %{x}: %{z:.2f}<extra></extra>")) if len(hm) else empty("Not enough data"); f1 = sty(f1, 420, "Spearman relationship heatmap: top 15 drivers by lag")
    sel = sel if sel in Ww.columns else (tp.driver.iloc[0] if len(tp) else None); sl = int(sl or 0); f2 = empty("No driver"); f3 = empty("No driver")
    if sel:
        y = Ww[o].diff() if diff else Ww[o]; x = (Ww[sel].diff() if diff else Ww[sel]).shift(sl); m = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
        if len(m) >= 5: cf = np.polyfit(m.x, m.y, 1); xs = np.linspace(m.x.min(), m.x.max(), 20); f2 = go.Figure([go.Scatter(x=m.x, y=m.y, mode="markers", name="Months", marker=dict(color=C["mid"], size=8)), go.Scatter(x=xs, y=cf[0] * xs + cf[1], name="Linear trend", line=dict(color=C["go"], width=3))]); f2 = sty(f2, 340, "%s (lag %d) vs %s%s: n=%d" % (sel, sl, o, " (changes)" if diff else "", len(m))); f2.update_xaxes(title=sel); f2.update_yaxes(title=o)
        if len(m) >= 18: rl = pd.Series([stats.spearmanr(m.x.iloc[i - 12:i], m.y.iloc[i - 12:i])[0] for i in range(12, len(m) + 1)], index=m.index[11:]); f3 = sty(go.Figure(go.Scatter(x=rl.index, y=rl.values, line=dict(color=C["mid"], width=3))), 300, "Rolling 12-month Spearman: is the relationship stable?"); f3.update_yaxes(range=[-1, 1])
    return h, f1, f2, f3
@safe(3)
def render_drv(seg, per, win, thr, o, k):
    R = getR(seg, per, win, thr); D = G["D"]; o = o or "gross_margin_pct"; m = driver_model(D, o, R["drivers"], R["per"], int(win), int(k or 5)); h = banner()
    if not m["ok"]: return h + note("Driver modelling disabled: " + esc(m["why"]), "warn"), None, None
    s = m["split"]; h += note("<b>Explanatory vs predictive.</b> Predictive test: drivers are taken from the <b>previous month</b> and each segment's KPIs are standardised using <b>training months only</b>; train = months before %s (%d rows, latest %s), test = %s onward (%d rows); no random split. Drivers are screened on the training period only. Metrics are in standardised units (σ). 'Skill' = 1 − MAE ÷ MAE of the naive previous-month forecast." % (mon(s[1]), m["n_tr"], mon(s[0]), mon(s[1]), m["n_te"]), "ai")
    h += tbl(m["perf"], [("model", "Model (held-out test)"), ("mae", "MAE (σ)"), ("rmse", "RMSE (σ)"), ("skill", "Skill vs naive")], dict(mae=lambda v: fx(v, 3), rmse=lambda v: fx(v, 3), skill=lambda v: sg(v))) + note("Models are reported together; none is chosen for looking best. A model that does not beat the naive forecast adds no predictive value%s." % (" (here the naive forecast is hard to beat)" if (m["perf"].skill.iloc[1:] <= 0).all() else ""), "info")
    h += SEC("Explanatory view: same-month standardised coefficients (OLS, all rows; intervals assume independent rows so they are optimistic)") + tbl(m["coef"], [("driver", "Driver"), ("beta", "Coefficient (σ per σ)"), ("lo", "95% low"), ("hi", "95% high"), ("vif", "VIF"), ("mech", "Arithmetic link")], dict(beta=lambda v: fx(v, 3), lo=lambda v: fx(v, 3), hi=lambda v: fx(v, 3), vif=lambda v: fx(v, 1), mech=lambda v: "yes" if v else "")) + note("Coefficients and feature importance describe association and model reliance, <b>not causal impact</b>. VIF above 5 signals multicollinearity.", "warn")
    h += SEC("Error analysis (Ridge, test period)") + tbl(m["byseg"], [("seg", "Segment"), ("e", "MAE (σ)")], dict(e=lambda v: fx(v, 3))) + tbl(m["top"].assign(period=m["top"].period.map(mon)), [("period", "Period"), ("seg", "Segment"), ("y", "Actual (σ)"), ("Ridge", "Predicted (σ)"), ("e", "Abs error")], dict(y=lambda v: fx(v, 2), Ridge=lambda v: fx(v, 2), e=lambda v: fx(v, 2)))
    p = m["pred"].groupby("period")[["y", "Naive", "Ridge", "RandomForest"]].mean(); f1 = go.Figure([go.Scatter(x=p.index, y=p[c], name=n, line=dict(width=3 if c == "y" else 2, color=cl)) for c, n, cl in (("y", "Actual", C["mid"]), ("Naive", "Naive", C["st"]), ("Ridge", "Ridge", C["go"]), ("RandomForest", "Random forest", C["li"]))]); f1 = sty(f1, 340, "Actual vs predicted on the held-out period (mean across segments, standardised)")
    i = m["imp"]; f2 = sty(go.Figure(go.Bar(y=i.feature, x=i.importance, orientation="h", marker_color=C["li"])), 320, "Random-forest feature reliance (not causation)"); f2.update_yaxes(autorange="reversed"); return h, f1, f2
@safe(3)
def render_imp(seg, per, win, thr):
    R = getR(seg, per, win, thr); b = R["br"]; h = banner()
    if b.get("err"): return h + note("Bridge unavailable: " + esc(b["err"]), "warn"), None, None
    S = b["S"]; per_t = "latest 3 months %s–%s vs prior 3 months %s–%s" % (mon(b["cur"][0]), mon(b["cur"][-1]), mon(b["prv"][0]), mon(b["prv"][-1])); rr = b["rows"]
    rows = [("Website traffic", "LMDI: L(f₁,f₀)·ln(T₁/T₀)", "website_traffic (sum)", rr["website_traffic"]), ("Conversion rate", "L(f₁,f₀)·ln(C₁/C₀)", "conversion_rate (mean)", rr["conversion_rate"]), ("Average order value", "L(f₁,f₀)·ln(A₁/A₀)", "aov (mean)", rr["aov"]), ("Not explained by formula", "actual Δrevenue − formula Δrevenue", "revenue, formula revenue", b["resid"]), ("Total revenue change", "R₁ − R₀", "revenue (sum)", b["dR"])]
    h += note("<b>Revenue bridge</b> (%s). Formula: <b>revenue ≈ traffic × conversion ÷ 100 × AOV ÷ 1000</b> per segment; the log-mean (LMDI) decomposition is exact and allocates the change with no double counting. Inputs are all <b>actual</b> values; no assumptions. The unexplained part is shown, not hidden." % per_t, "info") + tbl(pd.DataFrame(rows, columns=["s", "f", "m", "v"]).assign(share=lambda d: d.v / b["dR"] if b["dR"] else np.nan), [("s", "Step"), ("f", "Formula"), ("m", "Source metrics"), ("v", "Impact (₹k)"), ("share", "Share of change")], dict(v=lambda v: nf(v, 1), share=lambda v: pc(v)))
    rows2 = [("Volume (revenue change at prior margin)", "(R₁ − R₀) × GM₀", "revenue, gross margin", b["vol"]), ("Gross-margin rate", "R₁ × (GM₁ − GM₀)", "gross_profit ÷ revenue", b["rate"]), ("Operating expenses", "−(Opex₁ − Opex₀)", "opex", b["opx"]), ("Total operating-profit change", "sum of the three (identity)", "operating_profit", b["total"])]
    h += SEC("Operating-profit bridge (exact identity: OP = Revenue × GM − Opex)") + tbl(pd.DataFrame(rows2, columns=["s", "f", "m", "v"]), [("s", "Step"), ("f", "Formula"), ("m", "Source metrics"), ("v", "Impact (₹k)")], dict(v=lambda v: nf(v, 1))) + note("Check: bridge total %s ₹k vs actual operating-profit change %s ₹k. Gross margin %s → %s. These are measured arithmetic effects, <b>not causal estimates</b>; why traffic, conversion or margin moved needs separate investigation (see Relationship Explorer, which shows associations only). No monetary value is assigned to any correlation." % (nf(b["total"], 1), nf(b["dOP"], 1), pc(b["gm0"], 1), pc(b["gm1"], 1)), "ai")
    f1 = wf([rr["website_traffic"], rr["conversion_rate"], rr["aov"], b["resid"]], ["Traffic", "Conversion", "AOV", "Unexplained"], "Revenue bridge (₹k)"); f2 = wf([b["vol"], b["rate"], b["opx"]], ["Volume", "Margin rate", "Opex"], "Operating-profit bridge (₹k)"); return h, f1, f2
@safe(3)
def render_var(seg, per, win, thr):
    R = getR(seg, per, win, thr); c = R["cat"]; D = G["D"]; v = c[c.vb.notna()].assign(a=lambda d: d.vb.abs()).sort_values("a", ascending=False); mat = v[v.a >= R["thr"]]
    h = banner() + note("Variance % = (actual − budget) ÷ |budget|; materiality = %s (set above). Status is direction-aware. YoY needs 13+ months. Flags explain themselves and are not automatically errors." % pc(R["thr"]), "info") + SEC("Material variances in " + mon(R["per"]))
    h += tbl(mat.head(20), [("name", "KPI"), ("department", "Department"), ("cur_s", "Actual"), ("bud_s", "Budget"), ("vb", "vs budget"), ("mom", "vs prior month"), ("yoy", "vs year ago"), ("status", "Status")], dict(vb=sg, mom=sg, yoy=sg, status=pill)) if len(mat) else note("No KPI breaches the materiality threshold.", "ok")
    L = D["L"]; Lp = L[(L.period == R["per"]) & L.kpi_id.isin(["revenue", "gross_profit", "operating_profit", "opex"])]; sc = Lp.assign(var=Lp.actual - Lp.budget).pivot_table(index="segment", columns="kpi_id", values="var")
    if seg == "All" and len(sc) > 1: tot = sc.sum(); h += SEC("Segment contribution to total variance vs budget (₹k)") + tbl(sc.reset_index(), [("segment", "Segment")] + [(k, k.replace("_", " ")) for k in sc.columns], {k: lambda x: nf(x, 1) for k in sc.columns}) + note("Total variance: " + "; ".join("%s %s ₹k" % (k.replace("_", " "), nf(tot[k], 1)) for k in sc.columns), "info")
    an = R["an"].sort_values(["period", "z"], ascending=[False, False]).head(25); h += SEC("Anomaly log (last %d months)" % R["win"]) + (tbl(an, [("period", "Period"), ("kind", "Method"), ("kpi_id", "KPI"), ("value", "Value"), ("expected", "Expected"), ("z", "Score"), ("why", "Why it was flagged")], dict(period=mon, value=lambda x: nf(x, 1), expected=lambda x: nf(x, 1), z=lambda x: fx(x, 1))) if len(an) else note("No anomalies flagged.", "ok"))
    W, B = R["W"].tail(R["win"]), R["B"]; f1 = go.Figure([go.Scatter(x=W.index, y=W["operating_profit"], name="Operating profit actual", line=dict(color=C["mid"], width=3))] + ([go.Scatter(x=W.index, y=B["operating_profit"].reindex(W.index), name="Budget", line=dict(color=C["go"], dash="dot"))] if len(B) and "operating_profit" in B else [])) if "operating_profit" in W else empty("No operating profit"); f1 = sty(f1, 320, "Operating profit: actual vs budget (₹k)")
    f2 = sty(go.Figure(go.Bar(x=sc.index, y=sc["operating_profit"], marker_color=[C["sg"] if x >= 0 else C["co"] for x in sc["operating_profit"]])), 320, "Operating-profit variance vs budget by segment, " + mon(R["per"])) if (len(sc) and "operating_profit" in sc) else empty("No segment data"); return h, f1, f2
def ask(q, use_llm=False):
    if "D" not in G: return "Load data first."
    seg, per, win, thr = G.get("f") or ("All", G["D"]["pers"][-1].strftime("%Y-%m"), 36, 5); R = getR(seg, per, win, thr); nr = dict(narrative(R)); keys = list(nr); cat = R["cat"].set_index("kpi_id"); q = (q or "").strip() or "What changed?"; ql = q.lower(); parts = []
    mk = [k for k in cat.index if re.search(r"\b" + re.escape(k) + r"\b", ql) or cat.name[k].lower() in ql]
    if re.search(r"change|happen|moved|summary|brief", ql): parts += [keys[0], keys[1]]
    if re.search(r"driver|relat|associat|correl|explain|why", ql): parts.append(keys[2])
    if re.search(r"action|do|prior|next|recommend|should", ql): parts.append(keys[3])
    if re.search(r"evidence|limit|trust|confiden|caveat|support", ql): parts.append(keys[4])
    items = [(k, nr[k]) for k in dict.fromkeys(parts)]
    for k in mk[:2]: r = cat.loc[k]; items.append(("KPI detail: " + r["name"], "%s: actual %s, prior month %s (%s), budget %s (%s), status %s (direction: %s is better), 12-month trend %s, association with revenue rho %s (association only), data completeness %s." % (r["name"], fv(r.cur, r.unit), fv(r.prev, r.unit), sg(r.mom), r.bud_s, sg(r.vb), r.status, {"up": "higher", "down": "lower", "neutral": "no"}[r.direction], r.trend, fx(r.rho, 2), pc(r.compl))))
    if re.search(r"risk|anomal|unusual|opportun", ql): an = R["an"].head(4); items.append(("Risks and opportunities", "Unfavourable KPIs: " + (", ".join(R["cat"][(R["cat"].status == "Unfavourable") & ~R["cat"].kpi_id.isin(FIN)].name.head(5)) or "none") + ". Favourable: " + (", ".join(R["cat"][(R["cat"].status == "Favourable") & ~R["cat"].kpi_id.isin(FIN)].name.head(5)) or "none") + ". Anomalies: " + ("; ".join("%s %s" % (r.kpi_id, mon(r.period)) for r in an.itertuples()) or "none") + "."))
    if not items: items = [(keys[0], nr[keys[0]]), (keys[3], nr[keys[3]])]
    out = "### Answer (deterministic, computed from the loaded data)\n" + "\n".join("- **%s**: %s" % (a, b) for a, b in items) + "\n\n*Each figure comes from the active dataset and period; associations are not causes; scenarios are hypothetical; management judgement is required.*"
    if not use_llm: return out
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k: return out + "\n\n*External LLM disabled: no ANTHROPIC_API_KEY environment variable is set. The answer above is complete.*"
    try:
        ctx_ = "\n".join("[%s] %s" % (a, b) for a, b in items); r = requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"}, json={"model": "claude-sonnet-5-5", "max_tokens": 700, "system": "You are an executive analyst. Use ONLY the TOOL RESULTS. Never invent numbers, KPIs, causes or facts; keep every figure as given; say association, not cause.", "messages": [{"role": "user", "content": "TOOL RESULTS:\n" + ctx_ + "\n\nQUESTION: " + q}]}, timeout=60); r.raise_for_status()
        return "### LLM-written answer (structured results only, sent after you ticked the box)\n" + "".join(b.get("text", "") for b in r.json().get("content", [])) + "\n\n---\n" + out
    except Exception as e: return out + "\n\n*LLM call failed (%s); deterministic answer shown.*" % type(e).__name__
@safe(1)
def render_dec(seg, per, win, thr, w1, w2, w3, w4, w5, w6):
    R = getR(seg, per, win, thr); w = dict(impact=w1, urgency=w2, evidence=w3, effort=w4, feas=w5, risk=w6); A = score_actions(R["act"], w); G["A"] = A
    h = banner() + note("<b>Priority score (0-100)</b> = 100 × Σ weight × component ÷ Σ weights, with components: impact (measured ₹k, scaled to the largest; 0.3 neutral when no monetary evidence exists), urgency, evidence strength, ease (1 − effort), feasibility, safety (1 − risk). Urgency, effort, feasibility and risk are <b>documented heuristic assumptions</b> by action type. The score ranks attention; it is <b>not a probability of success</b>. Owners come from the KPI dictionary only.", "info")
    if A.empty: return h + note("No actions were generated for this view.", "ok")
    h += tbl(A, [("rank", "#"), ("id", "ID"), ("problem", "Problem"), ("action", "Recommended action"), ("owner", "Owner"), ("score", "Priority"), ("impact_k", "Impact ₹k"), ("basis", "Impact basis"), ("evidence", "Evidence"), ("impact_s", "Impact"), ("urg_s", "Urgency"), ("evid_s", "Evidence"), ("effort", "Effort"), ("feas", "Feasibility"), ("risk", "Risk")], dict(score=lambda v: fx(v, 0), impact_k=lambda v: nf(v, 0), impact_s=lambda v: fx(v, 2), urg_s=lambda v: fx(v, 2), evid_s=lambda v: fx(v, 2), effort=lambda v: fx(v, 2), feas=lambda v: fx(v, 2), risk=lambda v: fx(v, 2)))
    reg = pd.DataFrame(G.get("reg", [])); return h + SEC("Decision register (this session)") + (tbl(reg, [("id", "Action"), ("status", "Status"), ("rationale", "Rationale"), ("kpi", "Expected KPI outcome")]) if len(reg) else note("No decisions recorded yet.", "info"))
def update_reg(aid, st, rat, kpi):
    A = G.get("A")
    if A is None or aid not in set(A["id"]): return note("Choose an action ID that appears in the ranked list.", "warn")
    G["reg"] = [r for r in G.get("reg", []) if r["id"] != aid] + [dict(id=aid, status=st, rationale=rat or "", kpi=kpi or "")]; return note("Recorded for this session (exported with the decision register).", "ok") + tbl(pd.DataFrame(G["reg"]), [("id", "Action"), ("status", "Status"), ("rationale", "Rationale"), ("kpi", "Expected KPI outcome")])
@safe(3)
def render_scn(seg, per, win, thr, t_, c_, a_, g_, o_, v_, save):
    R = getR(seg, per, win, thr); W = R["W"].tail(3); need = ["revenue", "gross_profit", "opex"]
    if not set(need) <= set(W.columns) or W[need].isna().any().any(): raise ValueError("needs revenue, gross profit and operating expenses for the last 3 months.")
    b = dict(R=W.revenue.sum(), GP=W.gross_profit.sum(), OX=W.opex.sum()); lev = dict(t=float(t_ or 0), c=float(c_ or 0), a=float(a_ or 0), g=float(g_ or 0), o=float(o_ or 0)); v = float(v_ or 0) / 100
    sc = {n: scen_calc(b, lev, f, v) for n, f in (("Base (current run-rate)", 0), ("Downside (50% of assumptions realised)", .5), ("Scenario (assumptions as entered)", 1), ("Upside (150% realised)", 1.5))}
    if save: G.setdefault("scn_log", []).append(dict(period=mon(R["per"]), segment=seg, levers="traffic %+.1f%%, conversion %+.1f%%, AOV %+.1f%%, GM %+.1f pts, opex %+.1f%%, variable opex share %.0f%%" % (lev["t"], lev["c"], lev["a"], lev["g"], lev["o"], 100 * v), op_scenario=sc["Scenario (assumptions as entered)"]["op"], op_base=sc["Base (current run-rate)"]["op"]))
    h = banner() + note("<b>Assumption-based illustration, not a causal forecast.</b> Base = last 3 months (%s–%s). Revenue₁ = Revenue₀ × (1+traffic%%)(1+conversion%%)(1+AOV%%); gross profit₁ = Revenue₁ × (GM₀ + ΔGM); opex₁ = Opex₀ × [(1 − v) + v × Revenue₁/Revenue₀] × (1+opex%%), where v = %.0f%% is the share of opex assumed to vary with revenue (<b>your assumption</b>). Changing a KPI that is only correlated with revenue is not assumed to change revenue by itself." % (mon(R["W"].index[-3]), mon(R["per"]), 100 * v), "warn")
    rows = [("Revenue (₹k)", "rev", nf), ("Gross profit (₹k)", "gp", nf), ("Gross margin (%)", "gm", lambda x: fx(x, 1)), ("Operating expenses (₹k)", "ox", nf), ("Operating profit (₹k)", "op", nf), ("Operating margin (%)", "om", lambda x: fx(x, 1))]
    h += tbl(pd.DataFrame([[lab] + [fm(sc[n][k]) for n in sc] for lab, k, fm in rows], columns=["m"] + list(sc)), [("m", "Measure")] + [(n, n) for n in sc]) + SEC("Assumption table") + tbl(pd.DataFrame([("Website traffic change", "%+.1f%%" % lev["t"]), ("Conversion-rate change", "%+.1f%%" % lev["c"]), ("Average order value change", "%+.1f%%" % lev["a"]), ("Gross-margin change", "%+.1f pts" % lev["g"]), ("Operating-expense change", "%+.1f%%" % lev["o"]), ("Variable share of opex", "%.0f%%" % (100 * v))], columns=["a", "v"]), [("a", "Assumption"), ("v", "Value")])
    base_op = sc["Base (current run-rate)"]["op"]; sens = []
    for lab, k, d in (("Traffic ±10%", "t", 10), ("Conversion ±10%", "c", 10), ("AOV ±10%", "a", 10), ("Gross margin ±1 pt", "g", 1), ("Opex ±10%", "o", 10)):
        lo = scen_calc(b, dict(t=0, c=0, a=0, g=0, o=0, **{k: -d}), 1, v)["op"] - base_op; hi = scen_calc(b, dict(t=0, c=0, a=0, g=0, o=0, **{k: d}), 1, v)["op"] - base_op; sens.append((lab, lo, hi))
    log = pd.DataFrame(G.get("scn_log", [])); h += SEC("Saved scenarios (this session)") + (tbl(log, [("period", "Period"), ("segment", "Segment"), ("levers", "Assumptions"), ("op_base", "Base OP ₹k"), ("op_scenario", "Scenario OP ₹k")], dict(op_base=nf, op_scenario=nf)) if len(log) else note("None saved yet.", "info"))
    f1 = sty(go.Figure(go.Bar(x=[n.split(" (")[0] for n in sc], y=[sc[n]["op"] for n in sc], marker_color=[C["st"], C["co"], C["mid"], C["sg"]])), 320, "Operating profit over the 3-month base window by scenario (₹k, hypothetical)")
    f2 = go.Figure([go.Bar(y=[s[0] for s in sens], x=[s[1] for s in sens], orientation="h", name="Down", marker_color=C["co"]), go.Bar(y=[s[0] for s in sens], x=[s[2] for s in sens], orientation="h", name="Up", marker_color=C["sg"])]); f2.update_layout(barmode="overlay"); f2 = sty(f2, 320, "Sensitivity: change in operating profit (₹k) for one-at-a-time shocks"); return h, f1, f2
@safe(2)
def render_dq():
    D = G["D"]; h = banner() + note("Rows read: " + ", ".join("%s %s" % (TN[k], nf(v)) for k, v in D["rows_in"].items()) + ". Raw uploads stay unchanged; a validated copy is analysed. Excluded rows: <b>%d</b> (listed; nothing is dropped or imputed silently). Grain: monthly." % sum(c for _, _, c in D["excluded"]), "ok")
    h += "".join(note(esc(m), "err" if l == "error" else "warn" if l == "warn" else "info") for l, m in D["issues"]) or note("No validation issues.", "ok")
    if D["excluded"]: h += SEC("Excluded rows by reason") + tbl(pd.DataFrame(D["excluded"], columns=["t", "w", "c"]), [("t", "Table"), ("w", "Reason"), ("c", "Rows")], dict(c=nf))
    return h, SEC("Self-test results (run at start-up)") + "".join(note(("PASS " if ok else "FAIL ") + esc(g + ": " + n) + " — " + esc(d), "ok" if ok else "err") for g, n, ok, d in TESTS)
def export_all(seg, per, win, thr):
    if "D" not in G: return None, note("Load data first.")
    R = getR(seg, per, win, thr); out = []
    def w(df, fn):
        df.to_csv(fn, index=False)
        if os.path.exists(fn): out.append(fn)
    c = R["cat"]; w(c.drop(columns=["cur_s", "bud_s"]), "prism_kpi_catalogue.csv"); w(pd.concat([t.assign(outcome=o) for o, t in R["rel"].items()]) if R["rel"] else pd.DataFrame(), "prism_relationships.csv")
    m = driver_model(G["D"], "gross_margin_pct", R["drivers"], R["per"], int(win)); w(m["coef"].assign(outcome="gross_margin_pct") if m["ok"] else pd.DataFrame([dict(note=m["why"])]), "prism_driver_rankings.csv"); w(c[c.vb.notna()][["kpi_id", "name", "cur", "bud", "vb", "mom", "yoy", "status"]], "prism_variance.csv"); w(R["an"], "prism_anomalies.csv")
    A = score_actions(R["act"], DEFW); w(A, "prism_actions.csv"); w(pd.DataFrame(G.get("reg", [], ) or [dict(note="no decisions recorded")]), "prism_decision_register.csv"); w(pd.DataFrame(G.get("scn_log", []) or [dict(note="no scenarios saved")]), "prism_scenarios.csv")
    open("prism_executive_briefing.md", "w", encoding="utf-8").write("# PRISM AI — Executive briefing (%s, %s)\n\n%s\n\n" % (seg, mon(R["per"]), "_Synthetic demo data._" if G.get("demo") else "") + "\n\n".join("## %s\n%s" % (a, b) for a, b in narrative(R))); out.append("prism_executive_briefing.md"); return [f for f in out if os.path.exists(f)], note("Generated %d files for %s, %s (reproducible with the same inputs)." % (len(out), seg, mon(R["per"])), "ok")

# ------------------------------ self-tests ------------------------------
def setG(D, demo=True): G.clear(); G.update(D=D, demo=demo, ver=1, _c={})
def run_selftests(verbose=True):
    if TESTS: return TESTS
    Tt = []; saved = dict(G)
    def chk(g, n, fn):
        try: ok, d = fn(); Tt.append((g, n, bool(ok), d))
        except Exception as e: Tt.append((g, n, False, type(e).__name__ + ": " + str(e)[:90]))
    mini = lambda: dict(dic=pd.DataFrame(dict(kpi_id=["rev", "cost"], name=["Revenue", "Cost"], unit=["₹k", "₹k"], direction=["up", "down"], aggregation=["sum", "sum"])), ops=pd.DataFrame(dict(period=["2026-01-01", "2026-02-01", "2026-02-01", "2026-03-01", "2026-03-01", "2026-04-01"], segment="A", kpi_id=["rev", "rev", "rev", "rev", "zzz", "rev"], value=[10, 12, 13, "abc", 5, 14])))
    def t1():
        r = mini(); r["dic"] = r["dic"].drop(columns=["unit"])
        try: load_all(r); return False, "no error"
        except ValueError as e: return "unit" in str(e), "missing dictionary column reported with guidance"
    def t2(): D = load_all(mini()); w = " | ".join(m for _, m in D["issues"]); return len(D["L"]) == 3 and "duplicate" in w and "not in kpi_dictionary" in w and "non-numeric" in w and "Missing periods" in w, "duplicate, unknown KPI and non-numeric rows excluded; the missing month reported (never filled); 3 valid rows kept"
    def t3(): W = derive(pd.DataFrame(dict(revenue=[100.0, 200.0, 0.0], gross_profit=[40.0, 100.0, 5.0]))); return abs(W.gross_margin_pct[0] - 40) < 1e-9 and abs(W.gross_margin_pct[1] - 50) < 1e-9 and np.isnan(W.gross_margin_pct[2]), "gross margin 40% and 50%; zero revenue gives n/a, not infinity"
    def t4():
        r = demo_raw(); b = r["bud"].pivot_table(index=["period", "segment"], columns="kpi_id", values="budget"); D = demo_D(); bad = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in r.items()}; bad["fin"] = r["fin"].copy(); bad["fin"].loc[:, "gross_profit"] += 50; D2 = load_all(bad)
        return not any("reconciliation" in m for _, m in D["issues"]) and (b.gross_profit - (b.revenue - b.cogs)).abs().max() < 1e-6 and any("reconciliation" in m for _, m in D2["issues"]), "demo actuals and budgets reconcile; a corrupted gross profit is flagged and kept as supplied"
    def t5(): r = np.random.default_rng(1); x = r.standard_normal(40); W = pd.DataFrame(dict(x=x, y=pd.Series(x).shift(2).values + .01 * r.standard_normal(40))); T_ = rel_table(W, "y", ["x"], range(4), False).sort_values("spearman", key=abs, ascending=False); return int(T_.lag.iloc[0]) == 2 and T_.spearman.iloc[0] > .95, "a series built from x two months earlier is detected at lag 2 (rho %.2f)" % T_.spearman.iloc[0]
    def t6(): W = pd.DataFrame(dict(y=np.arange(30.0), c=np.ones(30), s=np.arange(30.0))); a = rel_table(W, "y", ["c"], [0], False); b = rel_table(W.head(8), "y", ["s"], [0], False); return np.isnan(a.spearman.iloc[0]) and a.strength.iloc[0] == "insufficient data" and np.isnan(b.spearman.iloc[0]), "constant variable and 8 observations give n/a, not a spurious correlation"
    def t7(): p = np.array([.001, .02, .04, .5]); q = bh(p); return (q >= p - 1e-12).all() and (q <= 1).all() and (np.diff(q) >= -1e-12).all(), "FDR q-values %s ≥ p and ordered" % np.round(q, 3)
    def t8(): D = demo_D(); m = driver_model(D, "gross_margin_pct", [c for c in wide(D["L"], D["K"]).columns if c not in FIN], D["pers"][-1], 36); return m["ok"] and m["split"][0] < m["split"][1] and abs(m["train_mean"]) < 1e-9 and abs(m["test_mean"]) > 1e-6, "train ends %s before test starts %s; standardisation uses training months only (train mean 0, test mean %.2f)" % (mon(m["split"][0]), mon(m["split"][1]), m["test_mean"])
    def t9(): return favour(.10, "down", .05) == "Unfavourable" and favour(-.10, "down", .05) == "Favourable" and favour(.03, "up", .05) == "On track" and favour(.2, "neutral", .05) == "On track", "a rise in a lower-is-better KPI is unfavourable; small and neutral moves are on track"
    def t10(): c = lmdi(180.0, 198.0, [(100, 120), (.03, .025), (60, 66)]); return abs(sum(c) - 18.0) < 1e-9, "contributions %s sum exactly to the change (18)" % np.round(c, 2)
    def t11(): D = demo_D(); b = bridges(D, "All", D["pers"][-1]); return b["err"] is None and abs(b["total"] - b["dOP"]) < 1e-6 and abs(sum(b["rows"].values()) - b["dRf"]) < 1e-6, "profit bridge %s = actual change %s; revenue factors add up to the formula change" % (nf(b["total"], 1), nf(b["dOP"], 1))
    def t12(): b = dict(R=1000.0, GP=400.0, OX=300.0); z = dict(t=0, c=0, a=0, g=0, o=0); a = scen_calc(b, z, 1, .0); u = scen_calc(b, dict(z, t=10), 1, 0.0); w = scen_calc(b, dict(z, t=10), 1, .5); return abs(a["op"] - 100) < 1e-9 and abs(u["rev"] - 1100) < 1e-9 and abs(u["op"] - 140) < 1e-9 and abs(w["op"] - 125) < 1e-9, "zero levers keep OP 100; +10% traffic gives revenue 1100, OP 140 (fixed opex) or 125 (50% variable opex)"
    def t13(): D = demo_D(); R = analyze(D, "All", D["pers"][-1], 36, .05); T_ = R["rel"]["gross_margin_pct"]; top = T_[T_.lag == 0].assign(a=lambda d: d.spearman.abs()).sort_values("a", ascending=False).head(3).driver.tolist(); return "otd_rate" in top, "planted driver found: top lag-0 drivers of gross margin = %s" % top
    def t14(): D = demo_D(); setG(D); f, _ = export_all("All", "2026-10", 36, 5); R = getR("All", "2026-10", 36, 5); n = len(pd.read_csv("prism_kpi_catalogue.csv")); G.clear(); G.update(saved); return n == len(R["cat"]) and "prism_executive_briefing.md" in f, "%d files written; catalogue export has %d rows matching the analysis" % (len(f), n)
    def t15(): D = demo_D(); setG(D); G["f"] = ("All", "2026-10", 36, 5); R = getR("All", "2026-10", 36, 5); a = ask("What changed?"); ok = "deterministic" in a and nf(R["cat"].set_index("kpi_id").cur["revenue"]) in a; G.clear(); G.update(saved); return ok, "briefing answers without any API and quotes the computed revenue figure"
    for g, n, f in [("registry", "missing dictionary column", t1), ("registry", "duplicates, unknown KPIs, gaps", t2), ("financial", "margin formula and zero revenue", t3), ("financial", "financial reconciliation", t4), ("financial", "direction-aware status", t9), ("relationship", "lag detection", t5), ("relationship", "constant and small samples", t6), ("relationship", "FDR correction", t7), ("relationship", "planted driver found", t13), ("driver", "chronological split, no leakage", t8), ("bridge", "exact LMDI decomposition", t10), ("bridge", "profit identity on demo", t11), ("scenario", "scenario recalculation", t12), ("reporting", "CSV export consistency", t14), ("reporting", "briefing grounded, no API", t15)]: chk(g, n, f)
    G.clear(); G.update(saved); TESTS[:] = Tt
    if verbose:
        for g, n, ok, d in Tt: print(("PASS " if ok else "FAIL ") + g + ": " + n + " :: " + d)
        print("Result: %d of %d self-tests passed." % (sum(1 for t in Tt if t[2]), len(Tt)))
    return TESTS

# ------------------------------ project export ------------------------------
ALGO = """## How PRISM AI works: the 10-step algorithm
1. **Ingest and map.** Load the four CSV tables (or the synthetic demo), map your column names to the schema, and keep the raw data unchanged.
2. **Validate and reconcile.** Check required fields, dates, numbers, duplicates, unknown KPI ids, units, missing months and the identities *gross profit = revenue − COGS* and *operating profit = gross profit − opex*. Problems are reported with row references; nothing is silently dropped or imputed.
3. **Standardise the grain.** Normalise to one monthly grain per segment, then apply the KPI registry: unit, direction (higher or lower is better), aggregation (sum or mean) and derived formulas such as margin percentages.
4. **Compute KPI facts.** For the chosen period: actual, prior month, year-on-year, budget variance, direction-aware status (favourable, unfavourable, on track), 12-month trend and data completeness.
5. **Detect variances and anomalies.** Apply the materiality threshold, then robust z-scores against a recent median and an Isolation Forest across all KPIs. Each flag explains itself; an unusual value is not assumed to be an error.
6. **Explain with arithmetic first.** Build an exact financial bridge: revenue = traffic × conversion × AOV (log-mean decomposition, no double counting) and operating profit = volume + margin rate + opex. Unexplained parts are shown, not hidden.
7. **Screen relationships.** Align KPIs by month and segment, test lags 0–3 with Pearson and Spearman, control false discoveries (Benjamini–Hochberg) and label each link supported, tentative or not supported. Association only, never causation.
8. **Model drivers chronologically.** Compare a naive baseline, a Ridge model and a random forest on a chronological train/test split with training-only standardisation and lagged features; report skill against the baseline; explain with coefficients and VIF.
9. **Turn evidence into decisions.** Generate candidate actions from variances, bridge contributors, supported drivers and anomalies; rank them with configurable weights for impact, urgency, evidence, effort, feasibility and risk. The score is a ranking aid, not a probability.
10. **Test, report and track.** Stress the plan in the scenario lab (base, downside, upside, sensitivity), write the briefing from the computed numbers, export CSV and Markdown, and record accept / reject / complete decisions for human review.
"""
METH = ALGO + """
### Notes
- Relationships use month-to-month changes by default (removes shared trends). p-values assume independent observations, so they are optimistic.
- The driver models are evaluated on held-out months in standardised units. Feature importance is model reliance, not causal impact.
- The bridge formula is exact for the stated decomposition; the 'not explained' term holds everything else.
- Scenarios are assumption-based illustrations. Changing an observational KPI is not assumed to change revenue on its own.
- Not included: Streamlit (Gradio is used), PDF export, hierarchical segments, a hosted open-source LLM.
"""
LICENSE = "MIT License\n\nCopyright (c) 2026 PRISM AI contributors\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n"
README = """# PRISM AI — Executive Decision Intelligence
Beyond the numbers. Into the decisions.

PRISM AI connects fragmented departmental KPIs to financial outcomes and turns the evidence into a prioritised, traceable decision workflow: KPI catalogue, relationship explorer, driver models, financial impact bridge, variance and anomaly intelligence, decision scoring and a scenario lab. The bundled data is **fictional synthetic data** (36 months, 6 departments, 36 KPIs, 3 segments, actual and budget) with a few planted relationships.

""" + ALGO + """
## Architecture
@@@mermaid
flowchart LR
  A[CSV upload or synthetic data] --> B[Validation + reconciliation]
  B --> C[KPI registry: direction, aggregation, formulas]
  C --> D[KPI facts + variance + anomalies]
  C --> E[Financial bridge]
  C --> F[Relationships: lags + FDR]
  F --> G[Chronological driver models]
  D --> H[Action scoring]
  E --> H
  F --> H
  H --> I[Scenario lab]
  H --> J[Briefing, exports, decision register]
@@@

## Run
@@@
pip install -r requirements.txt
python app.py
@@@
In Google Colab, paste `app.py` into one cell and run it. The `src/` modules in the brief are consolidated into `app.py`.

## Sample schemas
`financial_performance.csv` (period, segment, revenue, cogs, gross_profit, opex, operating_profit); `operational_kpis.csv` (period, segment, kpi_id, value); `budget_actuals.csv` (period, segment, kpi_id, actual, budget); `kpi_dictionary.csv` (kpi_id, name, department, category, unit, aggregation, direction, formula, frequency, owner, source).

## Tests and limits
`pip install pytest && pytest tests` runs the built-in self-tests. Associations are not causes; scenarios are hypothetical; the optional LLM is off by default and would only receive structured results. Add screenshots to `screenshots/` (none included).
""".replace("@@@", "`" * 3)
TFILE = "from app import run_selftests\n\n\ndef test_%s():\n    res = [r for r in run_selftests(verbose=False) if r[0] in %s]\n    assert res and all(r[2] for r in res), res\n"
def _src():
    try: return open(__file__, encoding="utf-8").read()
    except Exception: pass
    try:
        for s in list(get_ipython().user_ns.get("In") or [])[::-1]:
            if "PRISM AI — Executive Decision Intelligence" in s and "def main" in s: return s
    except Exception: pass
    return None
def write_samples():
    raw = demo_raw(); os.makedirs("sample_data", exist_ok=True); out = []; fn = dict(fin="financial_performance", ops="operational_kpis", bud="budget_actuals", dic="kpi_dictionary")
    for k, n in fn.items(): p = "sample_data/%s.csv" % n; raw[k].to_csv(p, index=False); out.append(p)
    return out
def build_project(files):
    root = "prism-ai-executive-intelligence"
    for d in ["sample_data", "tests", "docs", "screenshots"]: os.makedirs(os.path.join(root, d), exist_ok=True)
    src = _src()
    if src: open(root + "/app.py", "w", encoding="utf-8").write(src)
    for f in files: open(os.path.join(root, f), "wb").write(open(f, "rb").read())
    W = {"requirements.txt": "gradio>=4.44,<6\nplotly\nscikit-learn\nscipy\nrequests\npandas\nnumpy\n", "README.md": README, "LICENSE": LICENSE, ".gitignore": "__pycache__/\n.ipynb_checkpoints/\n*.zip\nprism_*.csv\nprism_*.md\n.env\n", "docs/methodology.md": METH,
         "docs/data_dictionary.md": "# Data dictionary\nSee README schemas. kpi_dictionary: aggregation = sum | mean | derived (how segments combine); direction = up (higher is better) | down | neutral. All samples are synthetic.\n", "docs/assumptions_and_limitations.md": "# Assumptions and limitations\nSynthetic data with planted relationships. Monthly grain only. Segment totals sum additive KPIs and average the rest (unweighted). p-values assume independent months. Action effort, feasibility and risk are heuristic defaults. Scenarios are assumption-based. Human review required.\n", "screenshots/README.md": "# Screenshots\nAdd your own screenshots here. None are included.\n"}
    for nm, g in [("kpi_registry", "registry"), ("financial_metrics", "financial"), ("relationship_engine", "relationship"), ("driver_analysis", "driver"), ("impact_bridge", "bridge"), ("scenarios", "scenario")]: W["tests/test_%s.py" % nm] = TFILE % (nm, "('%s',)" % g)
    for fn, tx in W.items(): open(os.path.join(root, fn), "w", encoding="utf-8").write(tx)
    z = "prism_ai_project.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for dp, _, fs in os.walk(root):
            for f in fs: zf.write(os.path.join(dp, f))
    return z, bool(src)

# ------------------------------ UI ------------------------------
CSS = """
.gradio-container{background:#F3F2EC!important;color:#202C36!important;font-family:Inter,system-ui,-apple-system,sans-serif!important;max-width:1400px!important}
.hdr{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;padding:24px 30px;border-radius:14px;background:#202C36;color:#F3F2EC;margin-bottom:12px}
.brand{display:flex;gap:16px;align-items:center}.logo{width:52px;height:52px;border-radius:12px;background:linear-gradient(135deg,#B8E3C7,#C9B8F0);color:#202C36;font-weight:800;font-size:22px;display:flex;align-items:center;justify-content:center}
.hdr h1{margin:0;font-size:28px;letter-spacing:3px;color:#F3F2EC}.hdr h1 span{color:#D7B878}.hdr p{margin:4px 0 0;color:#C9B8F0;font-style:italic}.badges span{display:inline-block;margin:3px;padding:4px 11px;border-radius:6px;background:#ffffff1a;color:#F3F2EC;font-size:12px}
button[role=tab]{background:#202C36!important;color:#F3F2EC!important;border-radius:8px 8px 0 0!important;margin-right:2px}button[role=tab][aria-selected=true]{background:#D7B878!important;color:#202C36!important;font-weight:700}
.kg{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:10px 0}.kc{background:#fff;border:1px solid #202C3626;border-radius:10px;padding:14px 16px}.kl{color:#5d6d78;font-size:11px;text-transform:uppercase;letter-spacing:1.1px}.kv{font-size:24px;font-weight:700;margin:6px 0 4px}.kd{color:#5d6d78;font-size:12px}
.note{background:#fff;padding:10px 14px;border-radius:8px;margin:8px 0;color:#202C36;font-size:14px;line-height:1.5;border:1px solid #202C3618}.sec{font-size:15px;font-weight:700;color:#202C36;margin:18px 0 6px;text-transform:uppercase;letter-spacing:1px}
.pill{display:inline-block;border-radius:99px;padding:2px 10px;font-size:11px;font-weight:700;color:#202C36;white-space:nowrap}.tw{overflow-x:auto;border-radius:8px;border:1px solid #202C3626;margin:8px 0;background:#fff}table{border-collapse:collapse;width:100%;font-size:13px}
th{background:#344650;color:#F3F2EC;text-align:left;padding:9px 10px;font-weight:600}td{padding:8px 10px;border-top:1px solid #202C3612;color:#202C36;vertical-align:top}tr:hover td{background:#B8E3C722}
button.primary{background:#202C36!important;color:#F3F2EC!important;border:none!important;font-weight:700!important}@media(max-width:640px){.hdr h1{font-size:21px}.kv{font-size:20px}}
"""
HEADER = "<div class='hdr'><div class='brand'><div class='logo'>PR</div><div><h1>PRISM <span>AI</span></h1><p>Beyond the numbers. Into the decisions.</p></div></div><div class='badges'><span>Associations, not causes</span><span>Scenarios are hypothetical</span><span>Priority ≠ probability</span><span>Works offline</span></div></div>"
def run_all(*a):
    try:
        files = a[:4]; mapping = a[4]; seed = int(a[5] or 7); demo = all(f is None for f in files)
        D = demo_D(seed) if (demo and not mapping) else load_all(demo_raw(seed) if demo else dict(zip(["fin", "ops", "bud", "dic"], [read_csv_any(f) if f is not None else None for f in files])), mapping); reg, sl = G.get("reg"), G.get("scn_log"); setG(D, demo)
        if reg: G["reg"] = reg
        if sl: G["scn_log"] = sl
        return note(("Fictional demo company analysed. " if demo else "Your data analysed. ") + "%d KPIs, %d segments, %d months (%s–%s)." % (len(D["K"]), len(D["segs"]), len(D["pers"]), mon(D["pers"][0]), mon(D["pers"][-1])), "ok")
    except Exception as e: return note("Could not complete the analysis: " + esc(e), "err")
def refresh():
    if "D" not in G: return tuple(gr.update() for _ in range(9))
    D = G["D"]; R = getR("All", D["pers"][-1].strftime("%Y-%m"), 36, 5); k = [(r.name, r.kpi_id) for r in R["cat"].itertuples()]; dv = [(x, x) for x in R["drivers"]]; ids = [("A%02d" % i) for i in range(1, 13)]
    return (gr.update(choices=["All"] + D["segs"], value="All"), gr.update(choices=[p.strftime("%Y-%m") for p in D["pers"]], value=D["pers"][-1].strftime("%Y-%m")), gr.update(choices=["All"] + sorted(R["cat"].department.unique()), value="All"), gr.update(choices=k, value=[]), gr.update(choices=k, value=k[0][1]), gr.update(choices=dv, value=[]), gr.update(choices=dv, value=dv[0][1] if dv else None), gr.update(choices=ids, value="A01"), gr.update(value=None))
def build_ui(zip_path, sfiles):
    with gr.Blocks(css=CSS, title="PRISM AI", theme=gr.themes.Base(primary_hue="slate", neutral_hue="stone")) as demo:
        gr.HTML(HEADER)
        with gr.Accordion("Filters: segment, reporting period, history window, materiality (apply to every page)", open=True):
            with gr.Row():
                f_s = gr.Dropdown(["All"], value="All", label="Segment"); f_p = gr.Dropdown([], label="Reporting period (month)"); f_w = gr.Slider(12, 36, 36, step=1, label="History window (months)"); f_t = gr.Slider(2, 20, 5, step=1, label="Materiality threshold (%)"); ap_btn = gr.Button("Apply filters", variant="primary")
        status = gr.HTML(note("Loading the fictional company, running analysis and self-tests (about 1 minute)...", "info")); FI = [f_s, f_p, f_w, f_t]
        with gr.Tabs():
            with gr.Tab("Executive Briefing"):
                b_h = gr.HTML()
                with gr.Row():
                    b1 = gr.Plot(); b2 = gr.Plot()
            with gr.Tab("KPI Intelligence"):
                with gr.Row():
                    k_d = gr.Dropdown(["All"], value="All", label="Department"); k_q = gr.Textbox(label="Search KPI, id or formula"); k_st = gr.Dropdown(["All", "Favourable", "Unfavourable", "On track"], value="All", label="Status"); k_c = gr.Dropdown([], multiselect=True, label="Compare KPIs"); k_x = gr.Dropdown([], label="Detail KPI"); k_btn = gr.Button("Update", variant="primary")
                k_h = gr.HTML()
                with gr.Row():
                    k1 = gr.Plot(); k2 = gr.Plot()
            with gr.Tab("Relationship Explorer"):
                with gr.Row():
                    r_o = gr.Dropdown(["revenue", "gross_profit", "operating_profit", "gross_margin_pct", "operating_margin_pct", "opex"], value="gross_margin_pct", label="Financial outcome"); r_d = gr.Dropdown([], multiselect=True, label="Candidate drivers (blank = all)"); r_l = gr.Slider(0, 6, 3, step=1, label="Maximum lag (months)"); r_df = gr.Checkbox(True, label="Use month-to-month changes (recommended)")
                with gr.Row():
                    r_s = gr.Dropdown([], label="Driver for scatter and rolling view"); r_sl = gr.Slider(0, 6, 0, step=1, label="Lag for scatter"); r_btn = gr.Button("Analyse", variant="primary")
                r_h = gr.HTML(); r1 = gr.Plot()
                with gr.Row():
                    r2 = gr.Plot(); r3 = gr.Plot()
            with gr.Tab("Driver Analysis"):
                with gr.Row():
                    d_o = gr.Dropdown(["revenue", "gross_profit", "operating_profit", "gross_margin_pct", "operating_margin_pct", "opex"], value="gross_margin_pct", label="Outcome"); d_k = gr.Slider(2, 8, 5, step=1, label="Drivers kept (chosen on training months)"); d_btn = gr.Button("Fit models", variant="primary")
                d_h = gr.HTML()
                with gr.Row():
                    d1 = gr.Plot(); d2 = gr.Plot()
            with gr.Tab("Financial Impact Bridge"):
                i_h = gr.HTML()
                with gr.Row():
                    i1 = gr.Plot(); i2 = gr.Plot()
            with gr.Tab("Variance & Anomalies"):
                v_h = gr.HTML()
                with gr.Row():
                    v1 = gr.Plot(); v2 = gr.Plot()
            with gr.Tab("Executive Strategist"):
                gr.Markdown("Answers are computed from the active data. Try: *What changed?* · *Which indicators are associated with margin?* · *What should management do next?* · *What is the evidence and what are the limits?* · *Tell me about conversion_rate* · *Any risks or anomalies?*")
                ag_q = gr.Textbox(label="Ask a question"); ag_l = gr.Checkbox(False, label="Use external LLM (off by default; sends only structured results; needs ANTHROPIC_API_KEY in the environment; check your data policy first)"); ag_b = gr.Button("Ask", variant="primary"); ag_o = gr.Markdown()
            with gr.Tab("Decision Centre"):
                with gr.Row():
                    w1 = gr.Slider(0, 1, .30, step=.05, label="Weight: impact"); w2 = gr.Slider(0, 1, .20, step=.05, label="Weight: urgency"); w3 = gr.Slider(0, 1, .20, step=.05, label="Weight: evidence"); w4 = gr.Slider(0, 1, .10, step=.05, label="Weight: ease (low effort)"); w5 = gr.Slider(0, 1, .10, step=.05, label="Weight: feasibility"); w6 = gr.Slider(0, 1, .10, step=.05, label="Weight: safety (low risk)")
                dc_btn = gr.Button("Re-score", variant="primary"); dc_h = gr.HTML()
                with gr.Row():
                    a_id = gr.Dropdown([], label="Action ID"); a_st = gr.Dropdown(["Under review", "Accepted", "Rejected", "Completed"], value="Under review", label="Status"); a_r = gr.Textbox(label="Decision rationale"); a_k = gr.Textbox(label="Expected KPI outcome"); a_b = gr.Button("Record decision")
                a_h = gr.HTML()
            with gr.Tab("Scenario & Sensitivity Lab"):
                gr.Markdown("Assumption-based illustration on the last 3 months. **Not a causal forecast.**")
                with gr.Row():
                    s1 = gr.Slider(-30, 30, 0, step=1, label="Website traffic (%)"); s2 = gr.Slider(-30, 30, 0, step=1, label="Conversion rate (%)"); s3 = gr.Slider(-20, 20, 0, step=1, label="Average order value (%)"); s4 = gr.Slider(-5, 5, 0, step=.5, label="Gross margin (percentage points)"); s5 = gr.Slider(-20, 20, 0, step=1, label="Operating expenses (%)"); s6 = gr.Slider(0, 100, 30, step=5, label="Share of opex that varies with revenue (%)")
                with gr.Row():
                    sc_b = gr.Button("Run scenario", variant="primary"); sv_b = gr.Button("Run and save to the session record")
                sc_h = gr.HTML()
                with gr.Row():
                    sc1 = gr.Plot(); sc2 = gr.Plot()
            with gr.Tab("Data Studio & Reports"):
                gr.Markdown("Upload CSVs: **kpi_dictionary** is required, plus **financial_performance** and/or **operational_kpis**; **budget_actuals** is optional. Leave empty for the fictional demo. Raw uploads are never modified.")
                up = []
                with gr.Row():
                    for k in ("fin", "ops", "bud", "dic"): up.append(gr.File(label=TN[k] + ".csv", file_types=[".csv"]))
                mp = gr.Textbox(label="Column mapping (only if auto-detect fails)", placeholder="kpi_id=metric, period=month", lines=2)
                with gr.Row():
                    seed = gr.Number(7, label="Demo seed"); ld_b = gr.Button("Validate and load", variant="primary"); rg_b = gr.Button("Regenerate demo")
                gr.File(value=sfiles, label="Sample CSVs (synthetic)", file_count="multiple", interactive=False); dq_h = gr.HTML(); t_h = gr.HTML()
                gr.Markdown("### Exports"); xp_b = gr.Button("Generate exports and executive briefing", variant="primary"); xp_m = gr.HTML(); xp_f = gr.File(label="Exports", file_count="multiple", interactive=False); gr.File(value=zip_path, label="Download GitHub-ready project (ZIP)", interactive=False)
            with gr.Tab("Methodology"):
                gr.Markdown(METH)
        RUN = up + [mp, seed]; KI = FI + [k_d, k_q, k_st, k_c, k_x]; RI = FI + [r_o, r_d, r_l, r_df, r_s, r_sl]; DI = FI + [d_o, d_k]; WI = FI + [w1, w2, w3, w4, w5, w6]; SI = FI + [s1, s2, s3, s4, s5, s6]
        def pages(e):
            e = e.then(render_brief, FI, [b_h, b1, b2]).then(render_kpi, KI, [k_h, k1, k2]).then(render_rel, RI, [r_h, r1, r2, r3]).then(render_drv, DI, [d_h, d1, d2]).then(render_imp, FI, [i_h, i1, i2])
            return e.then(render_var, FI, [v_h, v1, v2]).then(render_dec, WI, dc_h).then(lambda *a: render_scn(*a, False), SI, [sc_h, sc1, sc2]).then(render_dq, None, [dq_h, t_h])
        def full(ev): return pages(ev.then(refresh, None, [f_s, f_p, k_d, k_c, k_x, r_d, r_s, a_id, k_q]))
        full(ld_b.click(run_all, RUN, [status], show_progress="full")); full(demo.load(run_all, RUN, [status])); full(rg_b.click(lambda s: (s or 7) + 1, seed, seed).then(run_all, RUN, [status], show_progress="full"))
        pages(ap_b := ap_btn.click(lambda: None, None, None)); k_btn.click(render_kpi, KI, [k_h, k1, k2]); r_btn.click(render_rel, RI, [r_h, r1, r2, r3]); d_btn.click(render_drv, DI, [d_h, d1, d2]); dc_btn.click(render_dec, WI, dc_h); a_b.click(update_reg, [a_id, a_st, a_r, a_k], a_h)
        sc_b.click(lambda *a: render_scn(*a, False), SI, [sc_h, sc1, sc2]); sv_b.click(lambda *a: render_scn(*a, True), SI, [sc_h, sc1, sc2]); xp_b.click(export_all, FI, [xp_f, xp_m], show_progress="full"); ag_b.click(ask, [ag_q, ag_l], ag_o); ag_q.submit(ask, [ag_q, ag_l], ag_o)
    return demo
def main():
    sf = write_samples(); zp, saved = build_project(sf)
    print("=" * 78); print("PRISM AI starting. Demo data is FICTIONAL with planted relationships. No API key needed."); print("Running self-tests (about 1 minute):")
    demo_D(); run_selftests(verbose=True); demo = build_ui(zp, sf)
    print("Project ZIP:", zp, "| standalone app.py included:", "yes" if saved else "NO (create app.py yourself by pasting this cell into it)")
    print("Not included / not tested: Streamlit (Gradio used), PDF export, uploads of your own CSVs, the optional LLM. The public Gradio link is open to anyone: do not load confidential data.")
    print("=" * 78); demo.queue().launch(debug=False, show_error=True)
if __name__ == "__main__" or "google.colab" in sys.modules:
    main()