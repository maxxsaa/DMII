"""
Step 3: Community detection and global metrics.
Builds directed weighted graphs by year from the pharmaceutical trade data,
runs Louvain community detection (on undirected version), and computes
global network metrics. Outputs node partition and global metrics per year.
"""

import os
import pandas as pd
import networkx as nx

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs", "Step 3")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    """Load trade and country codes; add exporter/importer names."""
    df = pd.read_csv(os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv"))
    countries = pd.read_csv(os.path.join(DATA_DIR, "Country Codes V2026.csv"))
    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="i", right_on="country_code", how="left"
    )
    df = df.rename(columns={"country_name": "exporter"})
    df = df.merge(
        countries[["country_code", "country_name"]],
        left_on="j", right_on="country_code", how="left"
    )
    df = df.rename(columns={"country_name": "importer"})
    return df


def build_graph_for_year(df_year):
    """Build directed weighted graph from a year slice of trade df."""
    G = nx.DiGraph()
    for _, row in df_year.iterrows():
        exporter = row["exporter"]
        importer = row["importer"]
        weight = row["v"] if pd.notnull(row["v"]) else 0.0
        if pd.isna(exporter) or pd.isna(importer):
            continue
        if G.has_edge(exporter, importer):
            G[exporter][importer]["weight"] += weight
        else:
            G.add_edge(exporter, importer, weight=weight)
    return G


def run_louvain(G, weight="weight", seed=42):
    """Run Louvain on undirected version; return list of sets (communities)."""
    Gu = G.to_undirected()
    # Combine edge weights when converting directed -> undirected (sum)
    if Gu.number_of_edges() == 0:
        return []
    return list(nx.community.louvain_communities(Gu, weight=weight, seed=seed))


def main():
    print("Step 3: Community detection and global metrics")
    print("Loading data...")
    df = load_data()

    # Build graphs by year
    graphs_by_year = {}
    for year, df_year in df.groupby("t"):
        graphs_by_year[year] = build_graph_for_year(df_year)
    years = sorted(graphs_by_year.keys())
    print(f"  Built {len(years)} graphs (years {min(years)}–{max(years)})")

    # Community detection and global metrics per year
    rows_communities = []
    rows_global = []

    for year in years:
        G = graphs_by_year[year]
        Gu = G.to_undirected()

        # --- Louvain communities (on undirected graph) ---
        try:
            communities_list = run_louvain(G)
        except Exception as e:
            print(f"  Warning: Louvain failed for {year}: {e}")
            communities_list = []

        node_to_community = {}
        for cid, comm in enumerate(communities_list):
            for node in comm:
                node_to_community[node] = cid
        n_communities = len(communities_list)

        for node in G.nodes():
            rows_communities.append({
                "country": node,
                "year": year,
                "community_id": node_to_community.get(node, -1),
            })

        # --- Global metrics ---
        density = nx.density(G)
        try:
            clustering = nx.average_clustering(Gu, weight="weight")
        except Exception:
            clustering = None
        try:
            reciprocity = nx.reciprocity(G)
        except Exception:
            reciprocity = None
        if nx.is_connected(Gu):
            try:
                diameter = nx.diameter(Gu)
            except Exception:
                diameter = None
        else:
            diameter = None

        rows_global.append({
            "year": year,
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "n_communities": n_communities,
            "density": round(density, 6),
            "clustering_coefficient": round(clustering, 6) if clustering is not None else None,
            "reciprocity": round(reciprocity, 6) if reciprocity is not None else None,
            "diameter": diameter,
        })

    # Save outputs
    df_communities = pd.DataFrame(rows_communities)
    df_global = pd.DataFrame(rows_global)
    path_comm = os.path.join(OUTPUT_DIR, "communities_by_year.csv")
    path_global = os.path.join(OUTPUT_DIR, "global_metrics_by_year.csv")
    df_communities.to_csv(path_comm, index=False)
    df_global.to_csv(path_global, index=False)
    print(f"\nSaved:")
    print(f"  {path_comm} ({len(df_communities)} rows)")
    print(f"  {path_global} ({len(df_global)} rows)")


if __name__ == "__main__":
    main()
