"""
Step 1: Data analysis — Pharmaceutical Trade Dataset (BACI, HS 30).
Exploratory analysis and poster-ready visualizations for the DM II project.
Outputs figures suitable for the dataset section of an A0 poster.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# -----------------------------------------------------------------------------
# Paths: project root = parent of 'Python files'; Data and Outputs at project root
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# A0 poster: panels are often ~250–400 mm; use high DPI for print
POSTER_DPI = 150
FIG_SIZE_SINGLE = (10, 5.5)   # inches per panel
FIG_SIZE_WIDE = (12, 5.5)

# Style: readable at poster size (fonts scale when figure is placed on A0)
mpl.rcParams["font.size"] = 11
mpl.rcParams["axes.titlesize"] = 14
mpl.rcParams["axes.labelsize"] = 12
mpl.rcParams["xtick.labelsize"] = 10
mpl.rcParams["ytick.labelsize"] = 10
mpl.rcParams["legend.fontsize"] = 10


def load_data():
    """Load trade, country, and product reference tables."""
    trade = pd.read_csv(os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv"))
    countries = pd.read_csv(os.path.join(DATA_DIR, "Country Codes V2026.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "Codes produit HS92 2026.csv"))
    # BACI uses integer country codes; product codes are integers in CSV
    trade["i"] = trade["i"].astype(int)
    trade["j"] = trade["j"].astype(int)
    trade["k"] = trade["k"].astype(int)
    return trade, countries, products


def print_summary(trade, countries, products):
    """Print basic summary statistics to the console."""
    print("=" * 60)
    print("PHARMACEUTICAL TRADE DATASET — SUMMARY")
    print("=" * 60)
    print(f"Trade flows: {len(trade):,} rows")
    print(f"Years: {trade['t'].min()} – {trade['t'].max()}")
    print(f"Unique exporters: {trade['i'].nunique()}")
    print(f"Unique importers: {trade['j'].nunique()}")
    print(f"Unique products (HS 6-digit): {trade['k'].nunique()}")
    print(f"Total value (thousand USD): {trade['v'].sum():,.0f}")
    print(f"Value range: {trade['v'].min():.2f} – {trade['v'].max():,.2f} thousand USD")
    print(f"Missing quantity (q): {trade['q'].isna().sum():,}")
    print("=" * 60)


def fig_trade_value_by_year(trade, output_dir):
    """Total trade value (thousand USD) by year — time coverage for the poster."""
    by_year = trade.groupby("t", as_index=False)["v"].sum()
    by_year["v_billion"] = by_year["v"] / 1e6  # convert to billion USD for readability

    fig, ax = plt.subplots(figsize=FIG_SIZE_SINGLE, dpi=POSTER_DPI)
    ax.bar(by_year["t"], by_year["v_billion"], color="steelblue", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Trade value (billion USD)")
    ax.set_title("Pharmaceutical Trade Value by Year (HS 30, global)")
    ax.set_xticks(by_year["t"])
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "01_trade_value_by_year.png"), dpi=POSTER_DPI, bbox_inches="tight")
    fig.savefig(os.path.join(output_dir, "01_trade_value_by_year.pdf"), bbox_inches="tight")
    plt.close()
    print("Saved: 01_trade_value_by_year.png / .pdf")


def fig_top_exporters_importers(trade, countries, output_dir):
    """Top 15 exporters and top 15 importers by total value — two panels or one combined."""
    exp = trade.groupby("i")["v"].sum().sort_values(ascending=False).head(15)
    imp = trade.groupby("j")["v"].sum().sort_values(ascending=False).head(15)

    # Map country codes to names
    code_to_name = countries.set_index("country_code")["country_name"].to_dict()
    exp_names = [code_to_name.get(c, str(c)) for c in exp.index]
    imp_names = [code_to_name.get(c, str(c)) for c in imp.index]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_SIZE_WIDE, dpi=POSTER_DPI)
    # Exporters (horizontal bar)
    ax1.barh(range(len(exp_names)), exp.values / 1e6, color="teal", alpha=0.85)
    ax1.set_yticks(range(len(exp_names)))
    ax1.set_yticklabels(exp_names, fontsize=9)
    ax1.set_xlabel("Trade value (billion USD)")
    ax1.set_title("Top 15 Exporters (2016–2024)")
    ax1.invert_yaxis()

    ax2.barh(range(len(imp_names)), imp.values / 1e6, color="coral", alpha=0.85)
    ax2.set_yticks(range(len(imp_names)))
    ax2.set_yticklabels(imp_names, fontsize=9)
    ax2.set_xlabel("Trade value (billion USD)")
    ax2.set_title("Top 15 Importers (2016–2024)")
    ax2.invert_yaxis()

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "02_top_exporters_importers.png"), dpi=POSTER_DPI, bbox_inches="tight")
    fig.savefig(os.path.join(output_dir, "02_top_exporters_importers.pdf"), bbox_inches="tight")
    plt.close()
    print("Saved: 02_top_exporters_importers.png / .pdf")


def fig_product_breakdown(trade, products, output_dir):
    """Share of trade value by product (HS 4-digit). Top 10 + Other for poster clarity."""
    trade = trade.copy()
    trade["k4"] = trade["k"].astype(str).str[:4].astype(int)
    by_k4 = trade.groupby("k4")["v"].sum().sort_values(ascending=False)

    # Top 10 + Other
    n_top = 10
    top = by_k4.head(n_top)
    other_val = by_k4.iloc[n_top:].sum()
    if other_val > 0:
        top = pd.concat([top, pd.Series({"Other": other_val})])
    else:
        top = top.copy()

    prod_desc = products[products["code"].astype(str).str.startswith("30")].copy()
    prod_desc["k4"] = prod_desc["code"].astype(str).str[:4].astype(int)
    k4_to_desc = prod_desc.drop_duplicates("k4").set_index("k4")["description"].str[:45].to_dict()
    labels = [f"{k} – {k4_to_desc.get(k, 'Other')}" if k != "Other" else "Other product groups" for k in top.index]

    fig, ax = plt.subplots(figsize=FIG_SIZE_SINGLE, dpi=POSTER_DPI)
    wedges, texts, autotexts = ax.pie(
        top.values,
        labels=None,
        autopct="%1.1f%%",
        startangle=90,
        colors=plt.cm.Set3.colors[: len(top)],
        wedgeprops={"edgecolor": "white", "linewidth": 0.8},
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_title("Trade Value by Product Group (HS 4-digit)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "03_product_breakdown.png"), dpi=POSTER_DPI, bbox_inches="tight")
    fig.savefig(os.path.join(output_dir, "03_product_breakdown.pdf"), bbox_inches="tight")
    plt.close()
    print("Saved: 03_product_breakdown.png / .pdf")


def fig_value_distribution(trade, output_dir):
    """Distribution of flow values (log scale) — shows dominance of large flows."""
    v = trade["v"].dropna()
    v_pos = v[v > 0]

    fig, ax = plt.subplots(figsize=FIG_SIZE_SINGLE, dpi=POSTER_DPI)
    ax.hist(v_pos.clip(lower=0.1), bins=80, color="slategray", alpha=0.7, edgecolor="white", log=True)
    ax.set_xlabel("Flow value (thousand USD)")
    ax.set_ylabel("Count (log scale)")
    ax.set_title("Distribution of Trade Flow Values (2016–2024)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "04_value_distribution.png"), dpi=POSTER_DPI, bbox_inches="tight")
    fig.savefig(os.path.join(output_dir, "04_value_distribution.pdf"), bbox_inches="tight")
    plt.close()
    print("Saved: 04_value_distribution.png / .pdf")


def fig_dataset_overview_panel(trade, countries, output_dir):
    """Single composite figure: dataset overview for one poster panel (year + count stats)."""
    by_year = trade.groupby("t")["v"].sum() / 1e6  # billion USD
    n_flows = trade.groupby("t").size()
    n_exporters = trade.groupby("t")["i"].nunique()
    n_importers = trade.groupby("t")["j"].nunique()

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), dpi=POSTER_DPI, sharex=True)
    years = by_year.index.astype(int)

    ax1 = axes[0]
    ax1.bar(years - 0.2, by_year.values, width=0.4, label="Value (billion USD)", color="steelblue", alpha=0.9)
    ax1.set_ylabel("Trade value (billion USD)")
    ax1.set_title("Dataset Overview: Pharmaceutical Trade (HS 30, 2016–2024)")
    ax1.legend(loc="upper left")

    ax2 = axes[1]
    ax2.plot(years, n_flows.values / 1e3, "o-", color="darkgreen", label="Flows (thousands)", linewidth=2, markersize=6)
    ax2.plot(years, n_exporters.values, "s--", color="purple", label="Exporting countries", linewidth=1.5, markersize=5)
    ax2.plot(years, n_importers.values, "^--", color="orange", label="Importing countries", linewidth=1.5, markersize=5)
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Count")
    ax2.legend(loc="upper left", ncol=3)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "05_dataset_overview_panel.png"), dpi=POSTER_DPI, bbox_inches="tight")
    fig.savefig(os.path.join(output_dir, "05_dataset_overview_panel.pdf"), bbox_inches="tight")
    plt.close()
    print("Saved: 05_dataset_overview_panel.png / .pdf")


def main():
    print("Loading data...")
    trade, countries, products = load_data()

    print_summary(trade, countries, products)

    print("\nGenerating poster figures...")
    fig_trade_value_by_year(trade, OUTPUT_DIR)
    fig_top_exporters_importers(trade, countries, OUTPUT_DIR)
    fig_product_breakdown(trade, products, OUTPUT_DIR)
    fig_value_distribution(trade, OUTPUT_DIR)
    fig_dataset_overview_panel(trade, countries, OUTPUT_DIR)

    print(f"\nAll figures saved to: {OUTPUT_DIR}")
    print("Use PNG for slides, PDF for A0 poster print.")


if __name__ == "__main__":
    main()
