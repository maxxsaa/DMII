"""
Step 4: Layout and network visualization.

Builds directed weighted graphs from the pharmaceutical trade data (same
construction as steps 2–3), joins node-level metrics and community
partition, computes a 2D layout, and exports poster-ready network maps.

Outputs go to `Outputs/figures/` as high-resolution PNG and PDF files.
"""

import os
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import pandas as pd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs")
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Data loading and graph construction (mirrors step 3)
# ---------------------------------------------------------------------------

def load_trade_with_names() -> pd.DataFrame:
    """Load trade and country codes; add exporter/importer names."""
    trade_path = os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv")
    countries_path = os.path.join(DATA_DIR, "Country Codes V2026.csv")

    df = pd.read_csv(trade_path)
    countries = pd.read_csv(countries_path)

    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="i",
        right_on="country_code",
        how="left",
    ).rename(columns={"country_name": "exporter"})

    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="j",
        right_on="country_code",
        how="left",
    ).rename(columns={"country_name": "importer"})

    return df


def build_directed_graph(df_slice: pd.DataFrame) -> nx.DiGraph:
    """Build directed weighted graph from a trade DataFrame slice."""
    G = nx.DiGraph()

    for _, row in df_slice.iterrows():
        exporter = row["exporter"]
        importer = row["importer"]
        if pd.isna(exporter) or pd.isna(importer):
            continue

        weight = row["v"] if pd.notnull(row["v"]) else 0.0

        if G.has_edge(exporter, importer):
            G[exporter][importer]["weight"] += weight
        else:
            G.add_edge(exporter, importer, weight=weight)

    return G


def aggregate_over_years(df: pd.DataFrame, years: Iterable[int]) -> pd.DataFrame:
    """Return trade rows restricted to a set of years."""
    years = list(years)
    return df[df["t"].isin(years)].copy()


def subset_by_product_group(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """
    Split trade flows by product group.

    - "vaccines": HS6 codes starting with "3002"
    - "other": all remaining HS6 codes
    """
    k_str = df["k"].astype(str)
    if group == "vaccines":
        mask = k_str.str.startswith("3002")
    elif group == "other":
        mask = ~k_str.str.startswith("3002")
    else:
        raise ValueError(f"Unknown product group: {group}")
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Node attributes: metrics and communities
# ---------------------------------------------------------------------------

METRICS_PATH = os.path.join(OUTPUT_DIR, "metrics_by_year.csv")
COMMUNITIES_PATH = os.path.join(OUTPUT_DIR, "communities_by_year.csv")


def load_node_attributes_for_year(year: int) -> pd.DataFrame:
    """
    Load per-node attributes for a given year:
    - centrality metrics from `metrics_by_year.csv`
    - community_id from `communities_by_year.csv`
    """
    metrics = pd.read_csv(METRICS_PATH)
    comm = pd.read_csv(COMMUNITIES_PATH)

    metrics_year = metrics[metrics["year"] == year]
    comm_year = comm[comm["year"] == year]

    df_attrs = metrics_year.merge(
        comm_year[["country", "community_id"]],
        on="country",
        how="left",
    )
    return df_attrs


# ---------------------------------------------------------------------------
# Layout and visualization
# ---------------------------------------------------------------------------

def compute_layout(G: nx.Graph, seed: int = 42) -> Dict[str, Tuple[float, float]]:
    """
    Compute a 2D layout (spring layout on undirected version).

    Tweaked parameters to:
    - spread nodes further apart (larger k)
    - run more iterations for a cleaner layout
    - gently stretch the dense center so it occupies more space
    """
    Gu = G.to_undirected()
    n = max(Gu.number_of_nodes(), 1)
    # Default k is ~1 / sqrt(n); here we stretch the layout a bit more.
    k = 2.0 / (n ** 0.5)
    pos = nx.spring_layout(
        Gu,
        weight="weight",
        seed=seed,
        k=k,
        iterations=200,
        scale=1.0,
        center=(0.0, 0.0),
    )

    # Radial adjustment: expand the central cloud relative to outliers so that
    # most nodes occupy more of the canvas, while keeping outliers visible.
    if pos:
        xs = [xy[0] for xy in pos.values()]
        ys = [xy[1] for xy in pos.values()]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)

        # Max radius from center
        radii = []
        for x, y in pos.values():
            dx = x - cx
            dy = y - cy
            radii.append((dx ** 2 + dy ** 2) ** 0.5)
        max_r = max(radii) if radii else 0.0

        if max_r > 0:
            gamma = 0.5  # <1 expands central region relative to outer radius
            for node, (x, y) in pos.items():
                dx = x - cx
                dy = y - cy
                r = (dx ** 2 + dy ** 2) ** 0.5
                if r == 0:
                    continue
                r_norm = r / max_r
                r_new = (r_norm ** gamma) * max_r
                factor = r_new / r
                pos[node] = (cx + dx * factor, cy + dy * factor)

    return pos


def _scale_series(values: pd.Series, min_size: float, max_size: float) -> pd.Series:
    """Scale a numeric series to [min_size, max_size] for node sizes."""
    v = values.fillna(0.0)
    v_min = float(v.min())
    v_max = float(v.max())
    if v_max <= v_min:
        return pd.Series(min_size, index=v.index)
    scaled = (v - v_min) / (v_max - v_min)
    return min_size + scaled * (max_size - min_size)


# Default: show only top N nodes by total trade (in + out) for readability
TOP_N_NODES = 50


def _top_nodes_by_trade(G: nx.DiGraph, attrs: pd.DataFrame, n: int) -> List[str]:
    """Return the list of top `n` node names by total trade (in_degree + out_degree, weighted)."""
    attrs_idx = attrs.set_index("country")
    nodes = [u for u in G.nodes() if u in attrs_idx.index]
    if not nodes:
        return list(G.nodes())[:n]
    df = attrs_idx.loc[nodes]
    total_trade = (df["in_degree"].fillna(0) + df["out_degree"].fillna(0)).sort_values(
        ascending=False
    )
    return total_trade.head(n).index.tolist()


def draw_network(
    G: nx.DiGraph,
    attrs: pd.DataFrame,
    title: str,
    filename_prefix: str,
    seed: int = 42,
    top_n_nodes: Optional[int] = TOP_N_NODES,
) -> None:
    """
    Draw a network:
    - If top_n_nodes is set, only the top N nodes by total trade (and edges between them) are shown.
    - Nodes colored by community_id (legend added).
    - Nodes sized by betweenness centrality.
    - All visible nodes are labeled for readability.
    """
    if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
        print(f"Skipping {title}: empty graph.")
        return

    # Restrict to top N nodes by total trade for a readable, nameable graph
    attrs_idx = attrs.set_index("country")
    if top_n_nodes is not None and G.number_of_nodes() > top_n_nodes:
        top_list = _top_nodes_by_trade(G, attrs, top_n_nodes)
        G = G.subgraph(top_list).copy()
        attrs = attrs[attrs["country"].isin(top_list)]
        attrs_idx = attrs.set_index("country")
        title = f"{title} (top {len(top_list)} by trade)"

    nodes = list(G.nodes())
    if not nodes:
        print(f"Skipping {title}: no nodes after filtering.")
        return

    pos = compute_layout(G, seed=seed)

    # Community-based colors
    community = attrs_idx.reindex(nodes)["community_id"].fillna(-1).astype(int)
    unique_comms = sorted(community.unique())
    cmap = plt.get_cmap("tab20")
    color_map = {cid: cmap(i % cmap.N) for i, cid in enumerate(unique_comms)}
    node_colors = [color_map[cid] for cid in community]

    # Node sizes from betweenness
    betweenness = attrs_idx.reindex(nodes)["betweenness"]
    node_sizes = _scale_series(betweenness, min_size=120.0, max_size=1800.0)

    # Edge widths from weight
    weights = [G[u][v].get("weight", 0.0) for u, v in G.edges()]
    weights_series = pd.Series(weights)
    edge_widths = _scale_series(weights_series, min_size=0.15, max_size=2.5).tolist()

    fig, ax = plt.subplots(figsize=(18, 14))
    ax.set_axis_off()

    nx.draw_networkx_edges(
        G,
        pos,
        width=edge_widths,
        alpha=0.2,
        edge_color="grey",
        arrows=False,
        ax=ax,
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=node_sizes.tolist(),
        node_color=node_colors,
        linewidths=0.3,
        edgecolors="black",
        alpha=0.9,
        ax=ax,
    )

    # Label every node in the (possibly reduced) graph
    labels = {n: n for n in nodes}
    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=7,
        font_weight="bold",
        bbox=dict(boxstyle="round,pad=0.12", fc="white", alpha=0.85),
        ax=ax,
    )

    # Legend: community colors
    legend_handles = [
        mpatches.Patch(
            facecolor=color_map[cid],
            edgecolor="black",
            linewidth=0.5,
            label=f"Community {cid}" if cid >= 0 else "Other",
        )
        for cid in unique_comms
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper left",
        fontsize=9,
        framealpha=0.9,
        title="Louvain community",
    )

    ax.set_title(title, fontsize=16)
    fig.tight_layout()

    png_path = os.path.join(FIGURES_DIR, f"{filename_prefix}.png")
    pdf_path = os.path.join(FIGURES_DIR, f"{filename_prefix}.pdf")
    fig.savefig(png_path, dpi=400, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def generate_yearly_networks(df: pd.DataFrame) -> None:
    """Generate network maps for each individual year."""
    years = sorted(df["t"].unique())
    for year in years:
        df_year = df[df["t"] == year]
        G_year = build_directed_graph(df_year)
        attrs_year = load_node_attributes_for_year(year)
        title = f"Global pharmaceutical trade network, {year}"
        prefix = f"network_year_{year}"
        draw_network(G_year, attrs_year, title, prefix, seed=42)


def generate_period_networks(df: pd.DataFrame) -> None:
    """Generate network maps for pre-COVID vs COVID/post-COVID periods."""
    pre_years = [2016, 2017, 2018, 2019]
    post_years = [2020, 2021, 2022, 2023, 2024]

    # Pre-COVID
    df_pre = aggregate_over_years(df, pre_years)
    G_pre = build_directed_graph(df_pre)
    # Use average attributes over years as a simple proxy
    metrics = pd.read_csv(METRICS_PATH)
    comm = pd.read_csv(COMMUNITIES_PATH)
    attrs_pre = (
        metrics[metrics["year"].isin(pre_years)]
        .groupby("country", as_index=False)
        .mean(numeric_only=True)
        .merge(
            comm[comm["year"].isin(pre_years)]
            .groupby("country", as_index=False)["community_id"]
            .agg(lambda x: x.value_counts().idxmax()),
            on="country",
            how="left",
        )
    )
    draw_network(
        G_pre,
        attrs_pre,
        "Global pharmaceutical trade network, 2016–2019 (pre-COVID)",
        "network_period_2016_2019",
        seed=24,
    )

    # COVID / post-COVID
    df_post = aggregate_over_years(df, post_years)
    G_post = build_directed_graph(df_post)
    attrs_post = (
        metrics[metrics["year"].isin(post_years)]
        .groupby("country", as_index=False)
        .mean(numeric_only=True)
        .merge(
            comm[comm["year"].isin(post_years)]
            .groupby("country", as_index=False)["community_id"]
            .agg(lambda x: x.value_counts().idxmax()),
            on="country",
            how="left",
        )
    )
    draw_network(
        G_post,
        attrs_post,
        "Global pharmaceutical trade network, 2020–2024 (COVID/post-COVID)",
        "network_period_2020_2024",
        seed=25,
    )


def generate_product_group_networks(df: pd.DataFrame) -> None:
    """Generate network maps for vaccines vs other pharmaceutical products."""
    # Vaccines (HS 3002**)
    df_vacc = subset_by_product_group(df, "vaccines")
    if not df_vacc.empty:
        G_vacc = build_directed_graph(df_vacc)
        # Attributes averaged over all years for simplicity
        metrics = pd.read_csv(METRICS_PATH)
        comm = pd.read_csv(COMMUNITIES_PATH)
        attrs_vacc = (
            metrics.groupby("country", as_index=False)
            .mean(numeric_only=True)
            .merge(
                comm.groupby("country", as_index=False)["community_id"]
                .agg(lambda x: x.value_counts().idxmax()),
                on="country",
                how="left",
            )
        )
        draw_network(
            G_vacc,
            attrs_vacc,
            "Global pharmaceutical trade network — vaccines (HS 3002)",
            "network_vaccines_all_years",
            seed=52,
        )
    else:
        print("No vaccine (HS 3002**) flows found; skipping vaccines network.")

    # Other pharmaceutical products
    df_other = subset_by_product_group(df, "other")
    if not df_other.empty:
        G_other = build_directed_graph(df_other)
        metrics = pd.read_csv(METRICS_PATH)
        comm = pd.read_csv(COMMUNITIES_PATH)
        attrs_other = (
            metrics.groupby("country", as_index=False)
            .mean(numeric_only=True)
            .merge(
                comm.groupby("country", as_index=False)["community_id"]
                .agg(lambda x: x.value_counts().idxmax()),
                on="country",
                how="left",
            )
        )
        draw_network(
            G_other,
            attrs_other,
            "Global pharmaceutical trade network — other pharma (HS 30, excl. 3002)",
            "network_other_pharma_all_years",
            seed=53,
        )
    else:
        print("No non-vaccine pharmaceutical flows found; skipping other-pharma network.")


def main() -> None:
    print("Step 4: Layout and network visualization")
    print("Loading trade data...")
    df = load_trade_with_names()

    # Sanity check: required inputs from previous steps
    if not os.path.exists(METRICS_PATH) or not os.path.exists(COMMUNITIES_PATH):
        raise FileNotFoundError(
            "metrics_by_year.csv or communities_by_year.csv not found in Outputs/.\n"
            "Run step 2 (metrics_year_product) and step 3 (03_communities_global_metrics.py) first."
        )

    print("Generating yearly network maps...")
    generate_yearly_networks(df)

    print("Generating pre-/post-COVID period network maps...")
    generate_period_networks(df)

    print("Generating product-group (vaccines vs other pharma) network maps...")
    generate_product_group_networks(df)

    print("Step 4 complete. Figures saved in 'Outputs/figures/'.")


if __name__ == "__main__":
    main()

