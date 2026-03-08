# DM II Project — Pharmaceutical Trade Network Analysis

Data Mining II project: building and analyzing a **social network** of pharmaceutical trade flows between countries using **Gephi**, based on the CSV datasets in this folder.

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

## Project Goal

Use these pharmaceutical trade datasets to:

1. **Build a network** where nodes are countries (and optionally products) and edges are trade flows (value/quantity).
2. **Analyze the network** in Gephi (centrality, communities, structure, vulnerabilities).

---

## Workflow

### 1. Data analysis (Python)

- **Tool:** First Python script using **pandas** and **matplotlib**.
- **Goal:** Basic understanding of the files (dimensions, value/quantity distributions, main exporters/importers, product breakdown, temporal coverage).
- **Output:** Summary statistics and simple visualizations to guide the next step.

### 2. Data preparation for Gephi

- **Goal:** Export the trade network in Gephi’s expected format.
- **Script:** `Python files/02_prepare_gephi.py` — reads from `Data/`, writes to `Outputs/gephi/`.
- **Format (Gephi CSV):**
  - **Nodes table** (`nodes.csv`): columns **Id** (country code), **Label** (country name). One row per country that appears as exporter or importer.
  - **Edges table** (`edges.csv`): columns **Source** (exporter Id), **Target** (importer Id), **Weight** (total trade value in thousand USD), **Type** (`Directed`). One row per (exporter, importer) pair; value is summed over all years and products (or over a chosen year if you use the optional single-year export).
- **Output files (all written by one run of the script):**  
  - Full: `nodes.csv`, `edges.csv` (same as `nodes_all.csv`, `edges_all.csv`).  
  - Temporal: `nodes_YYYY.csv`, `edges_YYYY.csv` (each year 2016–2024); `nodes_2016_2019.csv`, `edges_2016_2019.csv`; `nodes_2020_2024.csv`, `edges_2020_2024.csv`.  
  - Product-level: `nodes_vaccines.csv`, `edges_vaccines.csv` (HS 3002); `nodes_other_pharma.csv`, `edges_other_pharma.csv`; same with suffixes `_2016_2019` and `_2020_2024` for period comparison.  
  See **GEPHI_GUIDELINES.md** for which files to use for each analysis.

### 3. Analysis in Gephi

- **Goal:** Import the prepared nodes and edges, then run a proper network analysis.
- **Steps to document in this README (to be detailed later):**
  - Import the graph (file format: CSV, GEXF, etc.).
  - Choose layout (e.g. Force Atlas 2, Yifan Hu).
  - Compute metrics (degree, weighted degree, betweenness, etc.).
  - Detect communities (e.g. Modularity).
  - Use size/color for metrics and interpret the pharmaceutical trade network (key players, clusters, vulnerabilities).

---

## Repository structure

- **Data/**  
  - `Pharmaceutical Trade Dataset.csv` — main trade flows (t, i, j, k, v, q).  
  - `Country Codes V2026.csv` — country code ↔ name.  
  - `Codes produit HS92 2026.csv` — product (HS) code descriptions.  
  - `Metadata_Pharmaceutical_Trade_Dataset_DMII.txt` — dataset description and filter.
- **Python files/**  
  - `01_data_analysis.py` — step 1: exploratory analysis and poster figures.  
  - `02_prepare_gephi.py` — step 2: build Gephi nodes/edges CSV from `Data/`.
- **Outputs/**  
  - `figures/` — poster-ready figures (PNG + PDF) from step 1.  
  - `gephi/` — Gephi-ready nodes/edges CSV (full, temporal by year and period, product-level vaccines and other pharma) from step 2.

---

*README will be updated as the analysis script, data preparation, and Gephi instructions are completed.*
