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

- **To implement in Python** (same pipeline, different graph variants).
- **Variants:** By period (2016–2019, 2020–2024), by year, by product group (vaccines HS 3002 vs other pharma). Compare rankings, communities, and global metrics across variants.
- **Output:** Tables and figures comparing structure over time and by product; short narrative (e.g. COVID-19 structural breaks).

### Step 6 — Sensitivity analysis

- **To implement in Python.**
- **Actions:** Exclude top N countries (by strength or betweenness), rebuild graph, recompute metrics and communities. Compare with full graph.
- **Output:** Summary of robustness (e.g. “rankings stable when top 5 exporters removed”) and optional comparison table/figure.

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
  - *(Steps 5–6: to be implemented in new or extended scripts.)*

- **Outputs/**  
  - `figures/` — poster-ready figures (PNG/PDF) from steps 1 and 4.  
  - `metrics_by_year.csv` — node-level metrics by year (step 2).  
  - `communities_by_year.csv` — node partition by year (step 3).  
  - `global_metrics_by_year.csv` — density, clustering, reciprocity, diameter per year (step 3).  
  - *(Further tables and figures from steps 4–6 as needed.)*

---

## How to run

1. **Environment:** `pip install -r requirements.txt` (pandas, matplotlib, networkx).
2. **Step 1:** `python "Python files/01_data_analysis.py"` → figures in `Outputs/figures/`.
3. **Step 2:** `python "Python files/metrics_year_product.py"` → `Outputs/metrics_by_year.csv`.
4. **Step 3:** `python "Python files/03_communities_global_metrics.py"` → `Outputs/communities_by_year.csv`, `Outputs/global_metrics_by_year.csv`.
5. **Step 4:** `python "Python files/04_layout_network_visualization.py"` → network maps in `Outputs/figures/`.
6. **Steps 5–6:** Implement and run as the pipeline is completed.

---

## Summary

| Step | What | Script / to do |
|------|------|-----------------|
| 1 | Exploratory analysis, dataset figures | `01_data_analysis.py` ✓ |
| 2 | Graphs + node metrics by year/product | `metrics_year_product.py` ✓ |
| 3 | Communities + global metrics | `03_communities_global_metrics.py` ✓ |
| 4 | Layout + network maps for poster | `04_layout_network_visualization.py` ✓ |
| 5 | Temporal + product comparison | To implement |
| 6 | Sensitivity (exclude top countries) | To implement |

All analysis and figures are produced in **Python**; no Gephi required.
