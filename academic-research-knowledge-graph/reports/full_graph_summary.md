# Full Academic Graph Summary

- Dataset: `data_final_pruned`
- Nodes: **8,452**
- 10 relationship types with at least one instance: **10/10**
- Base relationship records (internal citations only): **21,856**
- External citation rows excluded from CITES edges: **68,243**
- Derived relationship records: **32,948**
- Approx. distinct typed endpoint pairs: **53,694**

## Node types

| Type | Count |
|---|---:|
| Paper | 1,497 |
| Author | 4,575 |
| Institution | 1,229 |
| Topic | 482 |
| Venue | 669 |

## Relationships

| Type | Input rows / edges | Distinct typed endpoint pairs |
|---|---:|---:|
| AUTHORED | 5,797 | 5,797 |
| AFFILIATED_WITH | 6,281 | 5,171 |
| HAS_TOPIC | 4,491 | 4,491 |
| CITES | 3,821 | 3,821 |
| PUBLISHED_IN | 1,466 | 1,466 |
| CO_AUTHORED_WITH | 11,743 | 11,743 |
| RESEARCHES | 15,039 | 15,039 |
| COLLABORATES_WITH | 2,805 | 2,805 |
| BIBLIOGRAPHIC_COUPLING | 2,174 | 2,174 |
| CO_CITED_WITH | 1,187 | 1,187 |

## Interpretation

- CITES excludes cited papers outside the corpus; these external citations are metadata, not graph edges.
- AFFILIATED_WITH records can refer to multiple papers/years for the same Author–Institution pair.
- Distinct endpoint-pair counts are estimates for a one-edge-per-pair property graph schema; Neo4j counts depend on import rules.
- Derived evidence and weighting still require the separate audit_derived_edges.py verification.
- Zero automated issues is not evidence of >90% academic accuracy.

## Warnings

- No invalid derived endpoints/types were detected in this summary check.
