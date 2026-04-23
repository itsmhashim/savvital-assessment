#!/usr/bin/env python3
"""
CRM Sales Pipeline — Operations KPI Dashboard
Generates a self-contained interactive HTML file using Plotly.

Usage:
    pip install plotly pandas
    python dashboard.py

Output: dashboard.html (open in any browser, no server needed)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ---------------------------------------------------------------------------
# Data loading — looks for CSVs in ./data/ first, then the Kaggle folder
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
DATA_DIRS = [
    SCRIPT_DIR / "dataset",
    SCRIPT_DIR / "data",
    SCRIPT_DIR.parent / "CRM+Sales+Opportunities Kaggle Dataset",
]

DATA = next((d for d in DATA_DIRS if d.exists()), None)
if DATA is None:
    raise FileNotFoundError(
        "Could not find data folder. Place sales_pipeline.csv, "
        "sales_teams.csv, and products.csv in a 'data/' subfolder next to this script."
    )

pipeline = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
teams    = pd.read_csv(DATA / "sales_teams.csv")
products = pd.read_csv(DATA / "products.csv")

# ---------------------------------------------------------------------------
# Merge: add regional_office and product series to each deal
# Product names differ slightly between tables (e.g. "GTXPro" vs "GTX Pro")
# so we normalise the join key by stripping spaces.
# ---------------------------------------------------------------------------

pipeline["_key"] = pipeline["product"].str.replace(" ", "").str.lower()
products["_key"] = products["product"].str.replace(" ", "").str.lower()

df = (
    pipeline
    .merge(teams[["sales_agent", "regional_office"]], on="sales_agent", how="left")
    .merge(products[["_key", "series"]], on="_key", how="left")
)

# Derived columns
df["days_in_pipeline"] = (df["close_date"] - df["engage_date"]).dt.days
df["close_month"]      = df["close_date"].dt.to_period("M").astype(str)

won    = df[df["deal_stage"] == "Won"]
closed = df[df["deal_stage"].isin(["Won", "Lost"])]

# ---------------------------------------------------------------------------
# Metric calculations
# ---------------------------------------------------------------------------

# M1 — Pipeline volume by stage
STAGE_ORDER = ["Prospecting", "Engaging", "Won", "Lost"]
m1 = df["deal_stage"].value_counts().reindex(STAGE_ORDER).fillna(0).astype(int)

# M2 — Monthly win rate (Won / (Won + Lost) per close month)
m2 = (
    closed.groupby("close_month")
    .apply(lambda g: pd.Series({
        "deals": len(g),
        "wins":  (g["deal_stage"] == "Won").sum(),
    }))
    .assign(win_rate=lambda x: (x["wins"] / x["deals"] * 100).round(1))
    .reset_index()
    .sort_values("close_month")
)

# M3 — Avg days to close by individual product (Won deals only)
#      engage_date → close_date measures dwell time from first contact to close
#      Use canonical product name from products table via the normalised join key
m3 = (
    won.dropna(subset=["days_in_pipeline"])
    .merge(
        products[["_key", "product"]].rename(columns={"product": "product_name"}),
        on="_key", how="left"
    )
    .dropna(subset=["product_name"])
    .groupby("product_name")["days_in_pipeline"]
    .mean()
    .round(1)
    .sort_values()
    .reset_index()
    .rename(columns={"days_in_pipeline": "avg_days"})
)

# M4 — Monthly revenue from Won deals
m4 = (
    won.dropna(subset=["close_month", "close_value"])
    .groupby("close_month")["close_value"]
    .sum()
    .reset_index()
    .sort_values("close_month")
)

# M5 — Won deals by regional office (proxy for top acquisition channel)
m5 = won["regional_office"].value_counts().reset_index()
m5.columns = ["region", "deals"]
m5 = m5.sort_values("deals")

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

NAVY    = "#1B4F8A"
TEAL    = "#17A2B8"
GREEN   = "#27AE60"
ORANGE  = "#E67E22"
RED     = "#E74C3C"
PURPLE  = "#8E44AD"
PALETTE = [NAVY, TEAL, GREEN, ORANGE, PURPLE, RED]

# ---------------------------------------------------------------------------
# Build dashboard — 3×2 grid, bottom row spans full width
# ---------------------------------------------------------------------------

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=[
        "<b>Metric 1 — Pipeline Volume by Stage</b>",
        "<b>Metric 2 — Monthly Win Rate (%)</b>",
        "<b>Metric 3 — Won Deals by Sales Region</b>",
        "<b>Metric 4 — Monthly Revenue — Won Deals (USD)</b>",
        "<b>Metric 5 — Avg Days to Close by Product</b>",
        "",
    ],
    specs=[
        [{"type": "bar"},                      {"type": "scatter"}],
        [{"type": "domain"},                   {"type": "scatter"}],
        [{"type": "bar", "colspan": 2}, None],
    ],
    row_heights=[0.27, 0.33, 0.40],
    vertical_spacing=0.13,
    horizontal_spacing=0.10,
)

# --- M1: Pipeline volume bar ---
fig.add_trace(go.Bar(
    x=m1.index.tolist(),
    y=m1.values,
    marker_color=[NAVY, TEAL, GREEN, RED],
    text=m1.values,
    textposition="outside",
    showlegend=False,
    hovertemplate="%{x}: %{y} deals<extra></extra>",
), row=1, col=1)

# --- M2: Monthly win rate line ---
avg_wr = m2["win_rate"].mean()
fig.add_trace(go.Scatter(
    x=m2["close_month"],
    y=m2["win_rate"],
    mode="lines+markers",
    line=dict(color=TEAL, width=2.5),
    marker=dict(size=7, color=TEAL),
    fill="tozeroy",
    fillcolor="rgba(23,162,184,0.10)",
    showlegend=False,
    hovertemplate="%{x}: %{y}%<extra></extra>",
), row=1, col=2)
fig.add_hline(
    y=avg_wr, line_dash="dot", line_color="#999",
    annotation_text=f"Avg {avg_wr:.1f}%",
    annotation_font_color="#666",
    row=1, col=2,
)

# --- M3: Won deals by region — donut (row 2, col 1) ---
fig.add_trace(go.Pie(
    labels=m5["region"],
    values=m5["deals"],
    hole=0.45,
    marker=dict(colors=PALETTE[:len(m5)],
                line=dict(color="#ffffff", width=2)),
    textinfo="label+percent",
    textfont=dict(size=14),
    hovertemplate="%{label}: %{value} won deals (%{percent})<extra></extra>",
    showlegend=False,
), row=2, col=1)

# --- M4: Revenue area chart (row 2, col 2) ---
fig.add_trace(go.Scatter(
    x=m4["close_month"],
    y=m4["close_value"],
    mode="lines+markers",
    line=dict(color=GREEN, width=2.5),
    marker=dict(size=7, color=GREEN),
    fill="tozeroy",
    fillcolor="rgba(39,174,96,0.10)",
    showlegend=False,
    hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
), row=2, col=2)

# --- M5: Avg days by product — full-width horizontal bar (row 3) ---
fig.add_trace(go.Bar(
    x=m3["avg_days"],
    y=m3["product_name"],
    orientation="h",
    marker_color=PALETTE[:len(m3)],
    text=[f"{v:.0f} days" for v in m3["avg_days"]],
    textposition="outside",
    showlegend=False,
    hovertemplate="%{y}: %{x} days<extra></extra>",
), row=3, col=1)

# ---------------------------------------------------------------------------
# Layout & styling
# ---------------------------------------------------------------------------

fig.update_layout(
    title=dict(
        text=(
            "<b>CRM Sales Pipeline — Operations KPI Dashboard</b><br>"
            "<sup>Metrics: Volume by Stage · Win Rate · Deal Velocity · Revenue Trend · Regional Performance</sup>"
        ),
        x=0.5, xanchor="center",
        font=dict(size=20, color="#1B2631"),
    ),
    height=1420,
    paper_bgcolor="#F4F6F9",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Segoe UI, Arial, sans-serif", size=12, color="#2C3E50"),
    margin=dict(t=150, b=70, l=120, r=120),
)

# Axis labels
fig.update_yaxes(title_text="# Deals",       showgrid=True, gridcolor="#EAECEE", row=1, col=1)
fig.update_yaxes(title_text="Win Rate (%)",  showgrid=True, gridcolor="#EAECEE", row=1, col=2)
fig.update_yaxes(title_text="Revenue (USD)", showgrid=True, gridcolor="#EAECEE", tickformat="$,.0f", row=2, col=2)
fig.update_xaxes(title_text="Avg Days",      showgrid=True, gridcolor="#EAECEE", row=3, col=1)
fig.update_yaxes(automargin=True, tickfont=dict(size=12), showgrid=True, gridcolor="#EAECEE", row=3, col=1)

fig.update_xaxes(tickangle=45, showgrid=True, gridcolor="#EAECEE", row=1, col=2)
fig.update_xaxes(tickangle=45, showgrid=True, gridcolor="#EAECEE", row=2, col=2)

# Push subplot titles slightly away from the charts below them
for annotation in fig.layout.annotations:
    annotation.update(yshift=12)

# ---------------------------------------------------------------------------
# Export — HTML (always) + PDF (requires: pip install kaleido)
# ---------------------------------------------------------------------------

print_button_js = """
var btn = document.createElement('button');
btn.innerHTML = '&#8595; Download as PDF';
btn.style.cssText = [
    'position:fixed', 'top:60px', 'right:16px', 'z-index:9999',
    'padding:9px 18px', 'background:#1B4F8A', 'color:#fff',
    'border:none', 'border-radius:6px', 'font-size:13px',
    'cursor:pointer', 'font-family:Segoe UI,Arial,sans-serif',
    'box-shadow:0 2px 6px rgba(0,0,0,0.20)'
].join(';');
btn.onmouseover = function(){ this.style.background='#154080'; };
btn.onmouseout  = function(){ this.style.background='#1B4F8A'; };
btn.onclick = function(){ window.print(); };
document.body.appendChild(btn);
"""

out_html = SCRIPT_DIR / "dashboard.html"
fig.write_html(str(out_html), include_plotlyjs=True, full_html=True,
               post_script=print_button_js)

try:
    out_pdf = SCRIPT_DIR / "dashboard.pdf"
    fig.write_image(str(out_pdf), format="pdf", width=1400, height=1420)
    print(f"PDF saved:       {out_pdf}")
except Exception:
    print("PDF skipped — run: conda install -c plotly kaleido  then re-run script")

total_deals = len(df)
won_count   = len(won)
print(f"\nDataset loaded:  {total_deals:,} total deals | {won_count:,} won")
print(f"Dashboard saved: {out_html}")
print(f"Open in browser: {out_html.resolve()}\n")
