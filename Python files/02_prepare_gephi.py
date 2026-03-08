"""
Step 2: Data preparation for Gephi.
Builds nodes and edges CSV files from the pharmaceutical trade dataset.
Output format: Gephi-compatible CSV (Id, Label for nodes; Source, Target, Weight, Type for edges).

Exports:
- Full graph (all years, all products): nodes.csv, edges.csv
- Temporal: by year (nodes_YYYY.csv, edges_YYYY.csv); by period (2016_2019, 2020_2024)
- Product-level: vaccines (HS 3002) vs other pharma; each for all years and by period
"""

import os
import pandas as pd

# -----------------------------------------------------------------------------
# Paths: project root = parent of 'Python files'; Data and Outputs at project root
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs", "gephi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Product groups (HS 6-digit): vaccines = 300210–300290 (HS 3002); other = rest of HS 30
VACCINES_K_MIN = 300210
VACCINES_K_MAX = 300290
HS30_MIN = 300110
HS30_MAX = 300660


def load_data():
    """Load trade and country reference from Data/."""
    trade = pd.read_csv(os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv"))
    countries = pd.read_csv(os.path.join(DATA_DIR, "Country Codes V2026.csv"))
    trade["i"] = trade["i"].astype(int)
    trade["j"] = trade["j"].astype(int)
    trade["k"] = trade["k"].astype(int)
    return trade, countries


def filter_trade_product(trade: pd.DataFrame, product_group: str) -> pd.DataFrame:
    """
    Filter trade to a product group. In-place safe (returns a view/filtered copy).
    product_group: "all" | "vaccines" | "other_pharma"
    """
    k = trade["k"]
    if product_group == "all":
        return trade
    if product_group == "vaccines":
        return trade[(k >= VACCINES_K_MIN) & (k <= VACCINES_K_MAX)]
    if product_group == "other_pharma":
        # HS 30 excluding vaccines: 300110–300199 and 300310–300660
        return trade[((k >= HS30_MIN) & (k <= 300199)) | ((k >= 300310) & (k <= HS30_MAX))]
    raise ValueError(f"Unknown product_group: {product_group}")


def prepare_gephi_files(
    trade: pd.DataFrame,
    countries: pd.DataFrame,
    year_min=None,
    year_max=None,
) -> tuple:
    """
    Aggregate trade by exporter-importer and return Gephi nodes + edges DataFrames.

    - Nodes: all countries that appear as exporter or importer; Id = country code, Label = country name.
    - Edges: one row per (exporter, importer) with Weight = total trade value (thousand USD), Type = Directed.
    """
    t = trade.copy()
    if year_min is not None:
        t = t[t["t"] >= year_min]
    if year_max is not None:
        t = t[t["t"] <= year_max]
    if t.empty:
        return pd.DataFrame(columns=["Id", "Label"]), pd.DataFrame(columns=["Source", "Target", "Weight", "Type"])

    edges_df = t.groupby(["i", "j"], as_index=False)["v"].sum()
    edges_df = edges_df.rename(columns={"i": "Source", "j": "Target", "v": "Weight"})
    edges_df["Type"] = "Directed"

    node_ids = pd.unique(edges_df[["Source", "Target"]].values.ravel("K"))
    code_to_name = countries.set_index("country_code")["country_name"].to_dict()
    nodes_df = pd.DataFrame({"Id": node_ids})
    nodes_df["Label"] = nodes_df["Id"].map(lambda c: code_to_name.get(c, str(c)))
    return nodes_df, edges_df


def save_nodes_edges(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, base_name: str) -> None:
    """Write nodes and edges to Outputs/gephi/ with comma separator."""
    nodes_df.to_csv(os.path.join(OUTPUT_DIR, f"nodes_{base_name}.csv"), index=False, sep=",")
    edges_df.to_csv(os.path.join(OUTPUT_DIR, f"edges_{base_name}.csv"), index=False, sep=",")


def main():
    print("Loading data from Data/...")
    trade, countries = load_data()
    print(f"  Trade: {len(trade):,} rows, years {trade['t'].min()}–{trade['t'].max()}")

    # ----- 1. Full graph (all years, all products) -----
    nodes_df, edges_df = prepare_gephi_files(trade, countries)
    save_nodes_edges(nodes_df, edges_df, "all")
    print(f"\n[Full] nodes_all.csv, edges_all.csv — {len(nodes_df)} nodes, {len(edges_df)} edges")

    # ----- 2. Single-year graphs -----
    years = sorted(trade["t"].dropna().astype(int).unique())
    for y in years:
        n, e = prepare_gephi_files(trade, countries, year_min=y, year_max=y)
        save_nodes_edges(n, e, str(y))
    print(f"[Temporal — by year] nodes_YYYY.csv, edges_YYYY.csv for YYYY in {years}")

    # ----- 3. Period graphs (pre-COVID vs COVID/post-COVID) -----
    periods = [(2016, 2019, "2016_2019"), (2020, 2024, "2020_2024")]
    for y_min, y_max, tag in periods:
        n, e = prepare_gephi_files(trade, countries, year_min=y_min, year_max=y_max)
        save_nodes_edges(n, e, tag)
    print(f"[Temporal — by period] nodes_2016_2019.csv, edges_2016_2019.csv | nodes_2020_2024.csv, edges_2020_2024.csv")

    # ----- 4. Product-level: vaccines (HS 3002) -----
    trade_vacc = filter_trade_product(trade, "vaccines")
    if not trade_vacc.empty:
        n, e = prepare_gephi_files(trade_vacc, countries)
        save_nodes_edges(n, e, "vaccines")
        print(f"[Product — vaccines] nodes_vaccines.csv, edges_vaccines.csv — {len(n)} nodes, {len(e)} edges")
        for y_min, y_max, tag in periods:
            n_p, e_p = prepare_gephi_files(trade_vacc, countries, year_min=y_min, year_max=y_max)
            save_nodes_edges(n_p, e_p, f"vaccines_{tag}")
        print(f"  + vaccines_2016_2019, vaccines_2020_2024")
    else:
        print("[Product — vaccines] No data; skipping.")

    # ----- 5. Product-level: other pharma (HS 30 excluding vaccines) -----
    trade_other = filter_trade_product(trade, "other_pharma")
    if not trade_other.empty:
        n, e = prepare_gephi_files(trade_other, countries)
        save_nodes_edges(n, e, "other_pharma")
        print(f"[Product — other pharma] nodes_other_pharma.csv, edges_other_pharma.csv — {len(n)} nodes, {len(e)} edges")
        for y_min, y_max, tag in periods:
            n_p, e_p = prepare_gephi_files(trade_other, countries, year_min=y_min, year_max=y_max)
            save_nodes_edges(n_p, e_p, f"other_pharma_{tag}")
        print(f"  + other_pharma_2016_2019, other_pharma_2020_2024")
    else:
        print("[Product — other pharma] No data; skipping.")

    # Backward compatibility: keep nodes.csv / edges.csv as copies of all (so existing docs still work)
    nodes_df.to_csv(os.path.join(OUTPUT_DIR, "nodes.csv"), index=False, sep=",")
    edges_df.to_csv(os.path.join(OUTPUT_DIR, "edges.csv"), index=False, sep=",")
    print("\nAlso written: nodes.csv, edges.csv (same as nodes_all.csv, edges_all.csv)")

    print("\nGephi import: Data Laboratory → Import spreadsheet → load nodes first, then edges.")
    print("  Nodes: Id column = node id; Label = display name.")
    print("  Edges: Source, Target = node Ids; Weight = trade value; Type = Directed.")


if __name__ == "__main__":
    main()
