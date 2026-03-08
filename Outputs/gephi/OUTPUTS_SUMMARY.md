# Gephi outputs — summary

Generated after running `Python files/02_prepare_gephi.py`. All files are in `Outputs/gephi/`.

---

## Verification

- **nodes.csv / edges.csv:** 226 nodes, 20 836 edges — all Source/Target match node Ids.
- **nodes_2024.csv / edges_2024.csv:** 226 nodes, 12 866 edges — valid.

---

## Full graph (all years 2016–2024, all products)

| File        | Rows   | Description                    |
|------------|--------|---------------------------------|
| nodes.csv  | 226    | Countries (Id, Label)           |
| edges.csv  | 20 836 | Directed trade flows           |
| **Total weight** | **6 352 270 238** | Thousand USD (≈ 6.35 trillion USD) |

Same content: `nodes_all.csv`, `edges_all.csv`.

---

## Temporal — by year

| Year | Edges  | Nodes |
|------|--------|-------|
| 2016 | 12 897 | 226   |
| 2017 | 13 155 | 225   |
| 2018 | 13 198 | 226   |
| 2019 | 13 322 | 226   |
| 2020 | 13 464 | 226   |
| 2021 | 13 954 | 226   |
| 2022 | 13 926 | 226   |
| 2023 | 13 829 | 226   |
| 2024 | 12 866 | 226   |

---

## Temporal — by period (pre-COVID vs COVID/post-COVID)

| Period     | Edges  | Total weight (thousand USD) |
|------------|--------|-----------------------------|
| 2016–2019  | 17 221 | 2 265 711 529              |
| 2020–2024  | 18 586 | (larger period → more flows) |

---

## Product-level

| Graph           | Edges  | Nodes | Total weight (thousand USD) |
|-----------------|--------|-------|-----------------------------|
| **Vaccines** (HS 3002) | 12 746 | 226 | 2 242 101 656 |
| Vaccines 2016–2019     |  9 862 | 224 | — |
| Vaccines 2020–2024    | 11 412 | 226 | — |
| **Other pharma**      | 19 927 | 226 | — |
| Other pharma 2016–2019| 16 417 | 226 | — |
| Other pharma 2020–2024| 17 657 | 226 | — |

Vaccines account for a large share of value (≈ 2.24e9 thousand USD in the vaccines-only graph).

---

## Top trade flows (full graph, by weight)

1. Ireland → USA  
2. Germany → USA  
3. Switzerland → USA  
4. Switzerland → Germany  
5. USA → Germany  
6. Germany → Switzerland  
7. India → USA  
8. Netherlands → Germany  
9. Belgium → USA  
10. Ireland → Belgium  

---

## File count

- **38 CSV files** total: 19 node files + 19 edge files.
- Use **GEPHI_GUIDELINES.md** (project root) to choose which pair to import for each analysis (spatial, temporal, product, sensitivity).