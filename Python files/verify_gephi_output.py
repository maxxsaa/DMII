"""
Verify Gephi output files and show a short illustration of their content.
Run from project root or from 'Python files/'; reads from Outputs/gephi/.
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GEPHI_DIR = os.path.join(PROJECT_ROOT, "Outputs", "gephi")


def _read_csv(path, **kwargs):
    """Read CSV; auto-detect separator for robustness (comma vs semicolon)."""
    return pd.read_csv(path, sep=None, engine="python", **kwargs)


def main():
    print("=" * 60)
    print("GEPHI OUTPUT VERIFICATION & ILLUSTRATION")
    print("=" * 60)

    # Load all 4 files
    nodes = _read_csv(os.path.join(GEPHI_DIR, "nodes.csv"))
    edges = _read_csv(os.path.join(GEPHI_DIR, "edges.csv"))
    nodes_2024 = _read_csv(os.path.join(GEPHI_DIR, "nodes_2024.csv"))
    edges_2024 = _read_csv(os.path.join(GEPHI_DIR, "edges_2024.csv"))

    # Normalize column names (strip whitespace)
    for df in (nodes, edges, nodes_2024, edges_2024):
        df.columns = df.columns.str.strip()

    # Fix edges_2024 if it was saved with semicolon and broken header (e.g. "Source;;;" -> Source, Target, Weight, Type by position)
    for edf, name in [(edges_2024, "edges_2024")]:
        if "Target" not in edf.columns and edf.shape[1] >= 4:
            edf.columns = ["Source", "Target", "Weight", "Type"][: edf.shape[1]]

    # --- Verification ---
    def check(name, ndf, edf):
        ok = True
        if "Id" not in ndf.columns or "Label" not in ndf.columns:
            print(f"  [FAIL] {name} nodes: missing Id or Label")
            ok = False
        if "Source" not in edf.columns or "Target" not in edf.columns or "Weight" not in edf.columns:
            print(f"  [FAIL] {name} edges: missing Source, Target or Weight")
            ok = False
        if not ok:
            return
        node_ids = set(ndf["Id"].astype(int))
        src_ok = edf["Source"].astype(int).isin(node_ids).all()
        tgt_ok = edf["Target"].astype(int).isin(node_ids).all()
        if not (src_ok and tgt_ok):
            print(f"  [FAIL] {name}: some Source/Target not in nodes Id")
            ok = False
        else:
            print(f"  [OK] {name}: {len(ndf)} nodes, {len(edf)} edges; all Source/Target in nodes")
        return ok

    print("\nVerification:")
    check("All years (nodes.csv / edges.csv)", nodes, edges)
    check("Year 2024 (nodes_2024.csv / edges_2024.csv)", nodes_2024, edges_2024)

    # --- Illustration: tables ---
    print("\n" + "-" * 60)
    print("CONTENT ILLUSTRATION (all-years files)")
    print("-" * 60)

    print("\n1. Nodes — first 10 rows (Id = country code, Label = country name):")
    print(nodes.head(10).to_string(index=False))

    print("\n2. Edges — first 10 rows (Source → Target, Weight in thousand USD):")
    print(edges.head(10).to_string(index=False))

    print("\n3. Top 10 edges by weight (largest trade flows):")
    top_edges = edges.nlargest(10, "Weight").copy()
    # Add country names for readability
    id_to_label = nodes.set_index("Id")["Label"].to_dict()
    top_edges["Source_name"] = top_edges["Source"].map(id_to_label)
    top_edges["Target_name"] = top_edges["Target"].map(id_to_label)
    cols = ["Source", "Source_name", "Target", "Target_name", "Weight", "Type"]
    print(top_edges[cols].to_string(index=False))

    print("\n4. Summary stats:")
    print(f"   Total nodes (countries): {len(nodes)}")
    print(f"   Total edges (directed):  {len(edges)}")
    print(f"   Total weight (thousand USD): {edges['Weight'].sum():,.0f}")
    print(f"   Year 2024 — nodes: {len(nodes_2024)}, edges: {len(edges_2024)}")

    # List all Gephi CSVs (temporal + product from 02_prepare_gephi)
    csvs = sorted(f for f in os.listdir(GEPHI_DIR) if f.endswith(".csv"))
    if csvs:
        print("\n5. All Gephi CSV files in Outputs/gephi/:")
        for f in csvs:
            path = os.path.join(GEPHI_DIR, f)
            nlines = sum(1 for _ in open(path, "rb")) - 1  # exclude header
            print(f"   {f} ({nlines:,} rows)")
    # Quick check of period and product files if present
    for tag, f_edges in [("Period 2016–2019", "edges_2016_2019.csv"), ("Vaccines", "edges_vaccines.csv")]:
        p = os.path.join(GEPHI_DIR, f_edges)
        if os.path.isfile(p):
            edf = _read_csv(p)
            edf.columns = edf.columns.str.strip()
            if "Target" not in edf.columns and edf.shape[1] >= 4:
                edf.columns = ["Source", "Target", "Weight", "Type"][: edf.shape[1]]
            if "Source" in edf.columns and "Weight" in edf.columns:
                print(f"   [OK] {tag}: {len(edf)} edges, total weight {edf['Weight'].sum():,.0f} (thousand USD)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
