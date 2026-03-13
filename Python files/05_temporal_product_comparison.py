"""
Step 5: Temporal and product-level comparison.

Reads node-level metrics, communities, and global metrics produced by steps 2–3,
then rebuilds product-group graphs (vaccines vs other pharma) for each period to
compute product-specific metrics/communities.  Produces:

  - Figures comparing global metrics over time.
  - Figures comparing centrality rankings over time (top-10 bump chart).
  - Figures / tables comparing pre-COVID (2016–2019) vs COVID/post-COVID (2020–2024).
  - Figures / tables comparing vaccines (HS 3002) vs other pharma products.

Outputs go to `Outputs/figures/` (PNG + PDF) and `Outputs/` (CSV).
"""

import os
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import networkx as nx
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs", "Step 5")
FIGURES_DIR = OUTPUT_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)

METRICS_PATH = os.path.join(PROJECT_ROOT, "Outputs", "Step 2", "metrics_by_year.csv")
COMMUNITIES_PATH = os.path.join(PROJECT_ROOT, "Outputs", "Step 3", "communities_by_year.csv")
GLOBAL_METRICS_PATH = os.path.join(PROJECT_ROOT, "Outputs", "Step 3", "global_metrics_by_year.csv")


# ---------------------------------------------------------------------------
# Helper: save figure
# ---------------------------------------------------------------------------

def _save_fig(fig: plt.Figure, prefix: str) -> None:
    png = os.path.join(FIGURES_DIR, f"{prefix}.png")
    pdf = os.path.join(FIGURES_DIR, f"{prefix}.pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  Saved {png}")


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_trade_with_names() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv"))
    countries = pd.read_csv(os.path.join(DATA_DIR, "Country Codes V2026.csv"))
    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="i", right_on="country_code", how="left",
    ).rename(columns={"country_name": "exporter"})
    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="j", right_on="country_code", how="left",
    ).rename(columns={"country_name": "importer"})
    return df


def build_directed_graph(df_slice: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in df_slice.iterrows():
        exp, imp = row["exporter"], row["importer"]
        if pd.isna(exp) or pd.isna(imp):
            continue
        w = row["v"] if pd.notnull(row["v"]) else 0.0
        if G.has_edge(exp, imp):
            G[exp][imp]["weight"] += w
        else:
            G.add_edge(exp, imp, weight=w)
    return G


def compute_node_metrics(G: nx.DiGraph) -> pd.DataFrame:
    """Compute the same node-level metrics as step 2 for an arbitrary graph."""
    m = pd.DataFrame(index=list(G.nodes()))
    m["in_degree"] = pd.Series(dict(G.in_degree(weight="weight")))
    m["out_degree"] = pd.Series(dict(G.out_degree(weight="weight")))
    m["betweenness"] = pd.Series(nx.betweenness_centrality(G, weight="weight"))
    m["closeness"] = pd.Series(nx.closeness_centrality(G))
    m["degree_centrality"] = pd.Series(nx.degree_centrality(G))
    try:
        m["eigenvector"] = pd.Series(
            nx.eigenvector_centrality(G, weight="weight", max_iter=500)
        )
    except nx.PowerIterationFailedConvergence:
        m["eigenvector"] = None
    return m.reset_index().rename(columns={"index": "country"})


def compute_global_metrics(G: nx.DiGraph) -> Dict:
    Gu = G.to_undirected()
    density = nx.density(G)
    try:
        clustering = nx.average_clustering(Gu, weight="weight")
    except Exception:
        clustering = None
    try:
        reciprocity = nx.reciprocity(G)
    except Exception:
        reciprocity = None
    diameter = nx.diameter(Gu) if nx.is_connected(Gu) else None
    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "density": density,
        "clustering_coefficient": clustering,
        "reciprocity": reciprocity,
        "diameter": diameter,
    }


def run_louvain(G: nx.DiGraph, seed: int = 42) -> Dict[str, int]:
    """Louvain community detection; returns {node: community_id}."""
    Gu = G.to_undirected()
    if Gu.number_of_edges() == 0:
        return {n: 0 for n in G.nodes()}
    communities = list(nx.community.louvain_communities(Gu, weight="weight", seed=seed))
    mapping: Dict[str, int] = {}
    for cid, members in enumerate(communities):
        for node in members:
            mapping[node] = cid
    return mapping


# ===================================================================
# A) TEMPORAL COMPARISON  (uses pre-computed CSVs from steps 2–3)
# ===================================================================

def plot_global_metrics_over_time() -> None:
    """Line plots of density, clustering, reciprocity, #communities over the years."""
    gm = pd.read_csv(GLOBAL_METRICS_PATH)

    metrics_to_plot = [
        ("density", "Network density"),
        ("clustering_coefficient", "Avg. clustering coefficient"),
        ("reciprocity", "Reciprocity"),
        ("n_communities", "Number of Louvain communities"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.ravel()

    for ax, (col, label) in zip(axes, metrics_to_plot):
        ax.plot(gm["year"], gm[col], marker="o", linewidth=2)
        ax.set_ylabel(label, fontsize=11)
        ax.set_xlabel("Year", fontsize=11)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.grid(alpha=0.3)
        # Shade COVID onset
        ax.axvspan(2019.5, 2020.5, color="red", alpha=0.08, label="COVID onset")
        ax.legend(fontsize=8)

    fig.suptitle(
        "Global network metrics over time (2016–2024)", fontsize=14, y=1.01
    )
    fig.tight_layout()
    _save_fig(fig, "step5_global_metrics_over_time")


def plot_top_rankings_over_time(metric: str = "betweenness", top_k: int = 10) -> None:
    """Bump chart: rank of top-k countries over the years by a chosen metric."""
    df = pd.read_csv(METRICS_PATH)
    years = sorted(df["year"].unique())

    # Rank within each year (ascending rank = 1 is highest value)
    df["rank"] = df.groupby("year")[metric].rank(ascending=False, method="min")

    # Pick the top_k countries by average metric value across all years
    avg_metric = df.groupby("country")[metric].mean().nlargest(top_k)
    top_countries = avg_metric.index.tolist()
    sub = df[df["country"].isin(top_countries)]

    fig, ax = plt.subplots(figsize=(14, 8))
    for country, grp in sub.groupby("country"):
        grp = grp.sort_values("year")
        ax.plot(grp["year"], grp["rank"], marker="o", linewidth=1.8, label=country)
        # Label at last year
        last = grp.iloc[-1]
        ax.annotate(
            country,
            xy=(last["year"], last["rank"]),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=7,
            va="center",
        )

    ax.invert_yaxis()
    ax.set_ylabel(f"Rank by {metric}", fontsize=12)
    ax.set_xlabel("Year", fontsize=12)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.set_title(
        f"Top-{top_k} countries by {metric} — ranking over time",
        fontsize=14,
    )
    ax.axvspan(2019.5, 2020.5, color="red", alpha=0.08, label="COVID onset")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="lower left", ncol=2)
    fig.tight_layout()
    _save_fig(fig, f"step5_ranking_{metric}_over_time")


def plot_top_rankings_multi_metric(top_k: int = 10) -> None:
    """Side-by-side bump charts for the main centrality measures."""
    for metric in ["betweenness", "eigenvector", "degree_centrality"]:
        plot_top_rankings_over_time(metric=metric, top_k=top_k)


def compare_periods_rankings(top_k: int = 15) -> pd.DataFrame:
    """
    Compare average centrality rankings pre-COVID (2016-2019) vs
    COVID/post-COVID (2020-2024). Returns and saves a comparison table.
    """
    df = pd.read_csv(METRICS_PATH)

    pre = df[df["year"].between(2016, 2019)].groupby("country", as_index=False).mean(
        numeric_only=True
    )
    post = df[df["year"].between(2020, 2024)].groupby("country", as_index=False).mean(
        numeric_only=True
    )

    for period_df, tag in [(pre, "pre"), (post, "post")]:
        for col in ["betweenness", "eigenvector", "degree_centrality"]:
            period_df[f"rank_{col}"] = period_df[col].rank(
                ascending=False, method="min"
            )

    merged = pre[["country", "rank_betweenness", "rank_eigenvector", "rank_degree_centrality"]].merge(
        post[["country", "rank_betweenness", "rank_eigenvector", "rank_degree_centrality"]],
        on="country",
        suffixes=("_pre", "_post"),
    )
    for col in ["betweenness", "eigenvector", "degree_centrality"]:
        merged[f"rank_change_{col}"] = (
            merged[f"rank_{col}_pre"] - merged[f"rank_{col}_post"]
        )

    # Keep countries that are top_k in at least one period for at least one metric
    mask = (
        (merged["rank_betweenness_pre"] <= top_k)
        | (merged["rank_betweenness_post"] <= top_k)
        | (merged["rank_eigenvector_pre"] <= top_k)
        | (merged["rank_eigenvector_post"] <= top_k)
    )
    merged = merged[mask].sort_values("rank_betweenness_post")

    path = os.path.join(OUTPUT_DIR, "step5_period_ranking_comparison.csv")
    merged.to_csv(path, index=False)
    print(f"  Saved {path} ({len(merged)} rows)")
    return merged


def plot_period_comparison_bar() -> None:
    """Bar chart comparing key global metrics pre- vs post-COVID."""
    gm = pd.read_csv(GLOBAL_METRICS_PATH)
    pre = gm[gm["year"].between(2016, 2019)].mean(numeric_only=True)
    post = gm[gm["year"].between(2020, 2024)].mean(numeric_only=True)

    cols = ["density", "clustering_coefficient", "reciprocity"]
    labels = ["Density", "Clustering coeff.", "Reciprocity"]

    x = np.arange(len(cols))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [pre[c] for c in cols], width, label="Pre-COVID (2016–2019)")
    ax.bar(x + width / 2, [post[c] for c in cols], width, label="COVID/post (2020–2024)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Value", fontsize=11)
    ax.set_title("Global network metrics: pre-COVID vs COVID/post-COVID", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    _save_fig(fig, "step5_period_comparison_bar")


# ===================================================================
# B) PRODUCT-LEVEL COMPARISON  (vaccines HS 3002 vs other pharma)
# ===================================================================

def _product_subset(df: pd.DataFrame, group: str) -> pd.DataFrame:
    k_str = df["k"].astype(str)
    if group == "vaccines":
        return df[k_str.str.startswith("3002")].copy()
    else:
        return df[~k_str.str.startswith("3002")].copy()


def product_level_comparison(df_trade: pd.DataFrame) -> None:
    """
    Build graphs for vaccines vs other pharma (full period and by period),
    compute metrics, communities, and export comparison tables and figures.
    """
    periods = {
        "all_years": list(range(2016, 2025)),
        "pre_covid": [2016, 2017, 2018, 2019],
        "post_covid": [2020, 2021, 2022, 2023, 2024],
    }

    rows_global = []

    for period_label, years in periods.items():
        df_period = df_trade[df_trade["t"].isin(years)]

        for group in ["vaccines", "other"]:
            df_sub = _product_subset(df_period, group)
            if df_sub.empty:
                continue

            G = build_directed_graph(df_sub)
            gm = compute_global_metrics(G)
            gm["period"] = period_label
            gm["product_group"] = group

            comms = run_louvain(G)
            gm["n_communities"] = len(set(comms.values()))

            rows_global.append(gm)

            # Node metrics for this variant
            nm = compute_node_metrics(G)
            nm["period"] = period_label
            nm["product_group"] = group
            nm["community_id"] = nm["country"].map(comms)

            out_path = os.path.join(
                OUTPUT_DIR,
                f"step5_node_metrics_{group}_{period_label}.csv",
            )
            nm.to_csv(out_path, index=False)
            print(f"  Saved {out_path} ({len(nm)} rows)")

    df_global = pd.DataFrame(rows_global)
    global_path = os.path.join(OUTPUT_DIR, "step5_product_global_metrics.csv")
    df_global.to_csv(global_path, index=False)
    print(f"  Saved {global_path}")

    # --- Figure: grouped bar comparing vaccines vs other pharma ---
    plot_product_comparison_bars(df_global)

    # --- Figure: top-10 by betweenness for vaccines vs other ---
    plot_product_top_rankings(df_trade)


def plot_product_comparison_bars(df_global: pd.DataFrame) -> None:
    """Bar chart comparing global metrics for vaccines vs other pharma by period."""
    cols = ["density", "reciprocity", "n_communities"]
    labels = ["Density", "Reciprocity", "# Communities"]

    periods = ["pre_covid", "post_covid"]
    period_labels = ["Pre-COVID", "Post-COVID"]

    fig, axes = plt.subplots(1, len(cols), figsize=(16, 5), sharey=False)

    for ax, col, lab in zip(axes, cols, labels):
        x = np.arange(len(periods))
        width = 0.35

        vacc_vals = []
        other_vals = []
        for p in periods:
            row_v = df_global[
                (df_global["period"] == p) & (df_global["product_group"] == "vaccines")
            ]
            row_o = df_global[
                (df_global["period"] == p) & (df_global["product_group"] == "other")
            ]
            vacc_vals.append(float(row_v[col].iloc[0]) if len(row_v) else 0)
            other_vals.append(float(row_o[col].iloc[0]) if len(row_o) else 0)

        ax.bar(x - width / 2, vacc_vals, width, label="Vaccines (HS 3002)")
        ax.bar(x + width / 2, other_vals, width, label="Other pharma")
        ax.set_xticks(x)
        ax.set_xticklabels(period_labels, fontsize=10)
        ax.set_title(lab, fontsize=12)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle(
        "Network structure: vaccines vs other pharma (pre- and post-COVID)",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    _save_fig(fig, "step5_product_comparison_bars")


def plot_product_top_rankings(df_trade: pd.DataFrame, top_k: int = 10) -> None:
    """Horizontal bar chart showing top-k by betweenness for vaccines vs other (all years)."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=False)

    for ax, group, label in zip(
        axes,
        ["vaccines", "other"],
        ["Vaccines (HS 3002)", "Other pharma"],
    ):
        df_sub = _product_subset(df_trade, group)
        if df_sub.empty:
            ax.set_title(f"{label}: no data")
            continue

        G = build_directed_graph(df_sub)
        nm = compute_node_metrics(G)
        top = nm.nlargest(top_k, "betweenness")

        colors = plt.get_cmap("tab10")(np.linspace(0, 1, top_k))
        ax.barh(top["country"], top["betweenness"], color=colors)
        ax.invert_yaxis()
        ax.set_xlabel("Betweenness centrality", fontsize=11)
        ax.set_title(f"Top-{top_k} by betweenness — {label}", fontsize=12)
        ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    _save_fig(fig, "step5_product_top_betweenness")


# ===================================================================
# C) COMMUNITY STABILITY
# ===================================================================

def community_stability() -> None:
    """
    Measure how stable community assignments are across consecutive years
    using Normalised Mutual Information (NMI). Outputs a small table + plot.
    """
    from sklearn.metrics import normalized_mutual_info_score

    comm = pd.read_csv(COMMUNITIES_PATH)
    years = sorted(comm["year"].unique())

    rows = []
    for y1, y2 in zip(years[:-1], years[1:]):
        c1 = comm[comm["year"] == y1].set_index("country")["community_id"]
        c2 = comm[comm["year"] == y2].set_index("country")["community_id"]
        common = c1.index.intersection(c2.index)
        if len(common) == 0:
            continue
        nmi = normalized_mutual_info_score(c1.loc[common], c2.loc[common])
        rows.append({"year_pair": f"{y1}–{y2}", "nmi": round(nmi, 4)})

    df_nmi = pd.DataFrame(rows)
    path = os.path.join(OUTPUT_DIR, "step5_community_nmi.csv")
    df_nmi.to_csv(path, index=False)
    print(f"  Saved {path}")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_nmi["year_pair"], df_nmi["nmi"], color="steelblue")
    ax.set_ylabel("Normalised Mutual Information", fontsize=11)
    ax.set_xlabel("Year pair", fontsize=11)
    ax.set_title("Community stability across consecutive years (NMI)", fontsize=13)
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    _save_fig(fig, "step5_community_stability_nmi")


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    print("Step 5: Temporal and product-level comparison")

    for p in [METRICS_PATH, COMMUNITIES_PATH, GLOBAL_METRICS_PATH]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    # --- A) Temporal comparison ---
    print("\n[A] Global metrics over time...")
    plot_global_metrics_over_time()

    print("[A] Centrality rankings over time (bump charts)...")
    plot_top_rankings_multi_metric(top_k=10)

    print("[A] Period comparison: pre-COVID vs COVID/post-COVID...")
    compare_periods_rankings(top_k=15)
    plot_period_comparison_bar()

    # --- B) Product-level comparison ---
    print("\n[B] Product-level comparison (vaccines vs other pharma)...")
    df_trade = load_trade_with_names()
    product_level_comparison(df_trade)

    # --- C) Community stability ---
    print("\n[C] Community stability (NMI)...")
    try:
        community_stability()
    except ImportError:
        print("  scikit-learn not installed; skipping NMI computation.")

    print("\nStep 5 complete.")


if __name__ == "__main__":
    main()
