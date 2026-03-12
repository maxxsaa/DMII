# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 17:22:21 2026

@author: D0mTu
"""
import os
import pandas as pd
import networkx as nx

# Paths: project root = parent of 'Python files'; Data and Outputs at project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Import dataset (BACI trade flows)
df = pd.read_csv(os.path.join(DATA_DIR, "Pharmaceutical Trade Dataset.csv"))

# Import country codes and product codes
countries = pd.read_csv(os.path.join(DATA_DIR, "Country Codes V2026.csv"))
products = pd.read_csv(os.path.join(DATA_DIR, "Codes produit HS92 2026.csv"))

# Map cod códigos from countries by names
df = df.merge(countries[['country_code','country_name']], left_on='i', right_on='country_code', how='left')
df = df.rename(columns={'country_name':'exporter'})
df = df.merge(countries[['country_code','country_name']], left_on='j', right_on='country_code', how='left')
df = df.rename(columns={'country_name':'importer'})

# Mapear code by products (not working)
#df = df.merge(products[['code','description']], left_on='k', right_on='code', how='left')
#df = df.rename(columns={'description':'product'})

#############################################################
# Network by year or product
#############################################################

graphs_by_year = {}
for year, df_year in df.groupby('t'):
    G = nx.DiGraph()  # rede direcionada
    
    # Adicionar arestas com peso
    for _, row in df_year.iterrows():
        exporter = row['exporter']
        importer = row['importer']
        weight = row['v'] if pd.notnull(row['v']) else 0
        
        if G.has_edge(exporter, importer):
            G[exporter][importer]['weight'] += weight
        else:
            G.add_edge(exporter, importer, weight=weight, product=row['k'])
    
    graphs_by_year[year] = G

##################################################
## Year metrics by node
####################################################
metrics_by_year = {}
global_metrics_by_year = {}

# --- Metrics by node ---
for year, G in graphs_by_year.items():
    metrics = pd.DataFrame(index=G.nodes())
 
    # Grau (in/out)
    metrics['in_degree'] = dict(G.in_degree(weight='weight')).values()
    metrics['out_degree'] = dict(G.out_degree(weight='weight')).values()
    
    # Centralidade de intermediação
    metrics['betweenness'] = pd.Series(nx.betweenness_centrality(G, weight='weight'))
    
    # Centralidade de proximidade
    metrics['closeness'] = pd.Series(nx.closeness_centrality(G))  
    
    metrics['degree_centrality'] = pd.Series(nx.degree_centrality(G))
    
    # Eigenvector centrality (pode não convergir para grafos grandes)
    try:
        metrics['eigenvector'] = pd.Series(nx.eigenvector_centrality(G, weight='weight', max_iter=500))
    except nx.PowerIterationFailedConvergence:
        metrics['eigenvector'] = None
    
    # Eccentricity (precisa ser componente conectada; para grafos dirigidos podemos usar 'nx.eccentricity(G.to_undirected())')
    try:
        metrics['eccentricity'] = pd.Series(nx.eccentricity(G.to_undirected()))
    except nx.NetworkXError:
        metrics['eccentricity'] = None

    metrics['year'] = year
    metrics_by_year[year] = metrics.reset_index().rename(columns={'index':'country'})
    
    # --- Global Metrics ---
    global_metrics = {}
    if nx.is_connected(G.to_undirected()):
        global_metrics['diameter'] = nx.diameter(G.to_undirected())
#        global_metrics['radius'] = nx.radius(G.to_undirected())
#        global_metrics['average_geodesic_distance'] = nx.average_shortest_path_length(G, weight='weight')
    else:
        global_metrics['diameter'] = None
        global_metrics['radius'] = None
        global_metrics['average_geodesic_distance'] = None

    global_metrics['density'] = nx.density(G)
    global_metrics['clustering_coefficient'] = nx.average_clustering(G.to_undirected(), weight='weight')
    
    # Reciprocity (apenas para grafos direcionados)
    global_metrics['reciprocity'] = nx.reciprocity(G)
    
    global_metrics['year'] = year
    global_metrics_by_year[year] = pd.DataFrame([global_metrics])

##############################################
# HUBs per product
##############################################
product_name = 300490
df_product = df[df['k'] == product_name]

G_product = nx.DiGraph()
for _, row in df_product.iterrows():
    exporter = row['exporter']
    importer = row['importer']
    weight = row['v'] if pd.notnull(row['v']) else 0
    
    if G_product.has_edge(exporter, importer):
        G_product[exporter][importer]['weight'] += weight
    else:
        G_product.add_edge(exporter, importer, weight=weight)
        
# Calculate hubs (degree centrality)
degree_centrality = nx.degree_centrality(G_product)


final_df = pd.concat(metrics_by_year.values(), ignore_index=True)
final_df.to_csv(os.path.join(OUTPUT_DIR, "metrics_by_year.csv"), index=False)
