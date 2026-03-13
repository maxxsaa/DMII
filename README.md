# DM II Project — Pharmaceutical Trade Network Analysis

Data Mining II project: building and analyzing a **network** of pharmaceutical trade flows between countries using **Python** (pandas, NetworkX, matplotlib). Final deliverable: **A0 poster**.

---

## Dataset Summary

The data comes from **BACI** (CEPII’s international trade database at the product level):

- **Version:** 202601 | **Release date:** 2026-01-22  
- **Source:** [CEPII BACI](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37)

**Content:** Trade flows at **year × exporter × importer × product** level. Products use the **Harmonized System (HS) 6-digit** nomenclature. Values are in **thousand USD** and quantities in **metric tons**.

**Variables:**

| Variable | Description |
|----------|-------------|
| `t` | year |
| `i` | exporter (country code) |
| `j` | importer (country code) |
| `k` | product (HS 6-digit code) |
| `v` | value (thousand USD) |
| `q` | quantity (metric tons) |

**Filter applied:** Only HS codes starting with **30** (Pharmaceutical products, 300110–300660), including medical supplies, to study the **structure and vulnerabilities of global pharmaceutical trade networks** from **2016 to 2024**.

**Reference:** Gaulier, G. and Zignago, S. (2010), *BACI: International Trade Database at the Product-Level. The 1994-2007 Version*, CEPII Working Paper, N°2010-23.

---

## Project goal

1. **Build** directed, weighted networks: nodes = countries, edges = trade flows (value).
2. **Analyze** in Python: centrality, communities, layout, and visualization.
3. **Compare** over time (e.g. pre-COVID vs COVID/post-COVID), by product (vaccines vs other pharma), and test robustness (e.g. excluding top countries).
4. **Produce** poster-ready figures and tables (A0).

---

## Plan (Python-only workflow)

### Step 1 — Exploratory data analysis

- **Script:** `Python files/01_data_analysis.py`
- **Input:** `Data/` (trade, country codes, product codes).
- **Output:** `Outputs/figures/` — summary statistics and poster-ready plots (trade value by year, top exporters/importers, product breakdown, value distribution, dataset overview).
- **Purpose:** Describe the dataset used in the project (first part of the poster).

### Step 2 — Network construction and node-level metrics

- **Script:** `Python files/02_metrics_year_product.py` (existing).
- **Input:** `Data/` (trade, country codes).
- **Output:** `Outputs/metrics_by_year.csv` — per-country, per-year metrics (in/out degree, betweenness, closeness, degree centrality, eigenvector, etc.).
- **Purpose:** Build directed weighted graphs (by year and optionally by product), compute centralities; foundation for rankings and time series.

### Step 3 — Community detection and global metrics

- **Script:** `Python files/03_communities_global_metrics.py`
- **Input:** `Data/` (trade, country codes); builds same graphs as step 2 by year.
- **Actions:** Louvain community detection (on undirected weighted graph), global metrics (density, clustering coefficient, reciprocity, diameter) per year.
- **Output:** `Outputs/communities_by_year.csv` (country, year, community_id); `Outputs/global_metrics_by_year.csv` (year, n_nodes, n_edges, n_communities, density, clustering_coefficient, reciprocity, diameter).

### Step 4 — Layout and network visualization

- **Script:** `Python files/04_layout_network_visualization.py` (matplotlib + NetworkX).
- **Input:** Trade data (`Data/`), node metrics (`Outputs/metrics_by_year.csv`), communities (`Outputs/communities_by_year.csv`) from steps 2–3.
- **Actions:** Rebuild graphs, compute layout (spring layout with edge weights), draw networks (nodes colored by community, sized by centrality), and export high-resolution PNG/PDF suitable for the poster.
- **Output:** `Outputs/figures/` — network maps for each year, period comparisons (2016–2019 vs 2020–2024), and product subsets (vaccines vs other pharma).

### Step 5 — Temporal and product-level comparison

- **Script:** `Python files/05_temporal_product_comparison.py`
- **Input:** CSVs from steps 2–3 (`metrics_by_year.csv`, `communities_by_year.csv`, `global_metrics_by_year.csv`) + raw trade data for product-level graphs.
- **Actions:**
  - **(A) Temporal:** Global metrics over time (line plots), centrality bump charts (top-10 rankings by year), pre-COVID vs COVID/post-COVID bar comparison, period ranking table.
  - **(B) Product-level:** Build graphs for vaccines (HS 3002) vs other pharma for each period, compute metrics + communities, compare with grouped bar charts and top-10 tables.
  - **(C) Community stability:** NMI between consecutive years.
- **Output:** `Outputs/figures/step5_*.png|pdf`, `Outputs/step5_*.csv` (ranking tables, product-level metrics, NMI).

### Step 6 — Sensitivity analysis

- **Script:** `Python files/06_sensitivity_analysis.py`
- **Input:** Raw trade data (`Data/`).
- **Actions:** Sequentially remove the top-10 countries by total trade strength, rebuild graph, recompute global metrics (density, clustering, reciprocity, #communities) and betweenness rankings after each removal. Measure ranking stability via Spearman correlation. Run on year 2022 and on the all-years aggregated graph.
- **Output:** `Outputs/step6_*.csv` (global metrics and ranking comparison tables), `Outputs/figures/step6_*.png|pdf` (sensitivity figures).

---

## Repository structure

- **Data/**  
  - `Pharmaceutical Trade Dataset.csv` — main trade flows (t, i, j, k, v, q).  
  - `Country Codes V2026.csv` — country code ↔ name.  
  - `Codes produit HS92 2026.csv` — product (HS) code descriptions.  
  - `Metadata_Pharmaceutical_Trade_Dataset_DMII.txt` — dataset description and filter.

- **Python files/**  
  - `01_data_analysis.py` — step 1: exploratory analysis and poster figures.  
  - `metrics_year_product.py` — step 2: build graphs by year/product, compute node metrics, export `metrics_by_year.csv`.  
  - `03_communities_global_metrics.py` — step 3: Louvain communities and global metrics by year.  
  - `04_layout_network_visualization.py` — step 4: layout and network maps for poster.  
  - `05_temporal_product_comparison.py` — step 5: temporal, product-level, and community-stability comparisons.  
  - `06_sensitivity_analysis.py` — step 6: sensitivity analysis (sequential removal of top traders).

- **Outputs/** (one subfolder per step; all regenerated by the scripts)  
  - `Step 1/` — poster-ready figures (PNG/PDF) from exploratory analysis.  
  - `Step 2/` — `metrics_by_year.csv` (node-level metrics by year).  
  - `Step 3/` — `communities_by_year.csv`, `global_metrics_by_year.csv`.  
  - `Step 4/` — network maps (PNG/PDF) by year, period, and product group.  
  - `Step 5/` — comparison figures and tables (temporal, product-level, NMI).  
  - `Step 6/` — sensitivity analysis figures and tables.

---

## How to run

1. **Environment:** `pip install -r requirements.txt` (pandas, matplotlib, networkx, scikit-learn, scipy).
2. **Step 1:** `python "Python files/01_data_analysis.py"` → `Outputs/Step 1/`
3. **Step 2:** `python "Python files/02_metrics_year_product.py"` → `Outputs/Step 2/`
4. **Step 3:** `python "Python files/03_communities_global_metrics.py"` → `Outputs/Step 3/`
5. **Step 4:** `python "Python files/04_layout_network_visualization.py"` → `Outputs/Step 4/`
6. **Step 5:** `python "Python files/05_temporal_product_comparison.py"` → `Outputs/Step 5/`
7. **Step 6:** `python "Python files/06_sensitivity_analysis.py"` → `Outputs/Step 6/`

---

## Summary

| Step | What | Script / to do |
|------|------|-----------------|
| 1 | Exploratory analysis, dataset figures | `01_data_analysis.py` ✓ |
| 2 | Graphs + node metrics by year/product | `metrics_year_product.py` ✓ |
| 3 | Communities + global metrics | `03_communities_global_metrics.py` ✓ |
| 4 | Layout + network maps for poster | `04_layout_network_visualization.py` ✓ |
| 5 | Temporal + product comparison | `05_temporal_product_comparison.py` ✓ |
| 6 | Sensitivity (exclude top countries) | `06_sensitivity_analysis.py` ✓ |

All analysis and figures are produced in **Python**; no Gephi required.
