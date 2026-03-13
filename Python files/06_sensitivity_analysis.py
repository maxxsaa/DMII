"""
Step 6: Sensitivity analysis.

For a representative year (2022, latest full year before 2024 partial data)
and for the aggregated all-years graph:

  1. Build the full directed weighted graph.
  2. Identify the top-N countries by *total trade strength* (in + out weight).
  3. Remove them one-by-one (cumulative), rebuild the graph, and recompute
     global metrics (density, clustering, reciprocity, #communities) plus
     node-level centrality rankings.
  4. Compare with the full graph: do the remaining rankings stay stable?

Outputs:
  - Outputs/step6_sensitivity_global.csv   — global metrics after each removal.
  - Outputs/step6_sensitivity_rankings.csv — top-15 ranking comparison (full vs reduced).
  - Outputs/figures/step6_*.png|pdf        — poster-ready figures.
"""

import os
from typing import Dict, List, Tuple

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
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs", "Step 6")
FIGURES_DIR = OUTPUT_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers (same as previous steps)
# ---------------------------------------------------------------------------

def _save_fig(fig: plt.Figure, prefix: str) -> None:
    png = os.path.join(FIGURES_DIR, f"{prefix}.png")
    pdf = os.path.join(FIGURES_DIR, f"{prefix}.pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  Saved {png}")


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

    comms = []
    if Gu.number_of_edges() > 0:
        comms = list(nx.community.louvain_communities(Gu, weight="weight", seed=42))

    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "density": density,
        "clustering_coefficient": clustering,
        "reciprocity": reciprocity,
        "diameter": diameter,
        "n_communities": len(comms),
    }


def node_strength(G: nx.DiGraph) -> pd.Series:
    """Total trade (in + out weighted degree) per node."""
    in_w = pd.Series(dict(G.in_degree(weight="weight")))
    out_w = pd.Series(dict(G.out_degree(weight="weight")))
    return (in_w.add(out_w, fill_value=0)).sort_values(ascending=False)


def betweenness_ranking(G: nx.DiGraph) -> pd.Series:
    return pd.Series(nx.betweenness_centrality(G, weight="weight")).sort_values(
        ascending=False
    )


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def sensitivity_removals(
    G_full: nx.DiGraph,
    remove_order: List[str],
    max_removals: int = 10,
) -> Tuple[pd.DataFrame, List[pd.DataFrame]]:
    """
    Sequentially remove countries from the graph and recompute global metrics
    and betweenness rankings after each removal.

    Returns:
        global_rows: DataFrame with one row per removal step (including baseline).
        ranking_snapshots: list of DataFrames (betweenness rankings) per step.
    """
    G = G_full.copy()
    global_rows = []
    ranking_snapshots = []

    # Baseline (full graph)
    gm = compute_global_metrics(G)
    gm["removed"] = "none"
    gm["n_removed"] = 0
    global_rows.append(gm)

    bc = betweenness_ranking(G)
    snap = bc.reset_index()
    snap.columns = ["country", "betweenness"]
    snap["rank"] = range(1, len(snap) + 1)
    snap["removed"] = "none"
    ranking_snapshots.append(snap)

    removed_so_far: List[str] = []

    for i, country in enumerate(remove_order[:max_removals]):
        if country not in G.nodes():
            continue
        G.remove_node(country)
        removed_so_far.append(country)

        gm = compute_global_metrics(G)
        gm["removed"] = ", ".join(removed_so_far)
        gm["n_removed"] = len(removed_so_far)
        global_rows.append(gm)

        bc = betweenness_ranking(G)
        snap = bc.reset_index()
        snap.columns = ["country", "betweenness"]
        snap["rank"] = range(1, len(snap) + 1)
        snap["removed"] = ", ".join(removed_so_far)
        ranking_snapshots.append(snap)

    return pd.DataFrame(global_rows), ranking_snapshots


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def plot_global_sensitivity(df_global: pd.DataFrame, label: str) -> None:
    """Line plots of global metrics as countries are removed."""
    cols = [
        ("density", "Density"),
        ("reciprocity", "Reciprocity"),
        ("clustering_coefficient", "Clustering coeff."),
        ("n_communities", "# Communities"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.ravel()

    for ax, (col, title) in zip(axes, cols):
        ax.plot(df_global["n_removed"], df_global[col], marker="o", linewidth=2)
        ax.set_ylabel(title, fontsize=11)
        ax.set_xlabel("Countries removed (cumulative)", fontsize=11)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.grid(alpha=0.3)

    fig.suptitle(
        f"Sensitivity: global metrics after sequential removal of top traders ({label})",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _save_fig(fig, f"step6_global_sensitivity_{label}")


def plot_ranking_stability(
    ranking_snapshots: List[pd.DataFrame],
    remove_order: List[str],
    label: str,
    top_k: int = 15,
) -> None:
    """
    Show how the betweenness top-k changes as countries are removed.
    Two panels:
      - Left: rank of original top-k across removal steps.
      - Right: Spearman correlation of full top-k ranking with each reduced ranking.
    """
    baseline = ranking_snapshots[0]
    top_countries = baseline.head(top_k)["country"].tolist()

    # Filter out countries that will be removed so we track the "surviving" top-k
    tracked = [c for c in top_countries if c not in remove_order[: len(ranking_snapshots) - 1]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Panel 1: rank trajectory of surviving top-k countries
    steps = list(range(len(ranking_snapshots)))
    for country in tracked:
        ranks = []
        for snap in ranking_snapshots:
            row = snap[snap["country"] == country]
            ranks.append(int(row["rank"].iloc[0]) if len(row) else None)
        ax1.plot(steps, ranks, marker="o", linewidth=1.5, label=country)

    ax1.invert_yaxis()
    ax1.set_xlabel("Removal step", fontsize=11)
    ax1.set_ylabel("Betweenness rank", fontsize=11)
    ax1.set_title(f"Rank trajectory of top-{top_k} (surviving countries)", fontsize=12)
    ax1.legend(fontsize=7, loc="lower left", ncol=2)
    ax1.grid(alpha=0.3)
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # Panel 2: Spearman correlation of top-k ranking vs baseline
    from scipy.stats import spearmanr

    baseline_rank = baseline.set_index("country")["rank"]
    corrs = []
    for snap in ranking_snapshots:
        snap_rank = snap.set_index("country")["rank"]
        common = baseline_rank.index.intersection(snap_rank.index)
        if len(common) < 3:
            corrs.append(None)
            continue
        rho, _ = spearmanr(baseline_rank.loc[common], snap_rank.loc[common])
        corrs.append(rho)

    ax2.plot(steps, corrs, marker="s", linewidth=2, color="darkorange")
    ax2.set_xlabel("Removal step", fontsize=11)
    ax2.set_ylabel("Spearman ρ vs full graph", fontsize=11)
    ax2.set_title("Ranking correlation after removals", fontsize=12)
    ax2.set_ylim(0, 1.05)
    ax2.grid(alpha=0.3)
    ax2.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    fig.suptitle(
        f"Sensitivity: betweenness ranking stability ({label})",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _save_fig(fig, f"step6_ranking_stability_{label}")


def build_comparison_table(
    ranking_snapshots: List[pd.DataFrame],
    remove_order: List[str],
    label: str,
    top_k: int = 15,
) -> pd.DataFrame:
    """
    Table: for each surviving top-k country, show baseline rank vs rank after
    removing 5 and 10 countries.
    """
    baseline = ranking_snapshots[0].set_index("country")["rank"]
    steps_to_show = [0, min(5, len(ranking_snapshots) - 1), min(10, len(ranking_snapshots) - 1)]
    steps_to_show = sorted(set(steps_to_show))

    top_countries = baseline.sort_values().head(top_k).index.tolist()
    tracked = [c for c in top_countries if c not in remove_order[: len(ranking_snapshots) - 1]]

    rows = []
    for c in tracked:
        row = {"country": c}
        for step in steps_to_show:
            snap = ranking_snapshots[step].set_index("country")
            row[f"rank_after_{step}_removed"] = (
                int(snap.loc[c, "rank"]) if c in snap.index else None
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    path = os.path.join(OUTPUT_DIR, f"step6_ranking_comparison_{label}.csv")
    df.to_csv(path, index=False)
    print(f"  Saved {path} ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_sensitivity_for_graph(
    G: nx.DiGraph,
    label: str,
    max_removals: int = 10,
) -> None:
    """Full sensitivity pipeline for one graph."""
    strength = node_strength(G)
    remove_order = strength.head(max_removals).index.tolist()

    print(f"\n  Removal order ({label}): {remove_order}")

    df_global, ranking_snapshots = sensitivity_removals(G, remove_order, max_removals)

    # Save global metrics table
    path = os.path.join(OUTPUT_DIR, f"step6_sensitivity_global_{label}.csv")
    df_global.to_csv(path, index=False)
    print(f"  Saved {path}")

    # Figures
    plot_global_sensitivity(df_global, label)
    plot_ranking_stability(ranking_snapshots, remove_order, label)
    build_comparison_table(ranking_snapshots, remove_order, label)


def main() -> None:
    print("Step 6: Sensitivity analysis")
    print("Loading trade data...")
    df_trade = load_trade_with_names()

    # --- (A) Representative single year: 2022 ---
    print("\n[A] Sensitivity on year 2022...")
    df_2022 = df_trade[df_trade["t"] == 2022]
    G_2022 = build_directed_graph(df_2022)
    run_sensitivity_for_graph(G_2022, label="2022", max_removals=10)

    # --- (B) All-years aggregated graph ---
    print("\n[B] Sensitivity on all-years aggregated graph (2016–2024)...")
    G_all = build_directed_graph(df_trade)
    run_sensitivity_for_graph(G_all, label="all_years", max_removals=10)

    print("\nStep 6 complete.")


if __name__ == "__main__":
    main()
