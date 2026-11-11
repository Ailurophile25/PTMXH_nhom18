
from pathlib import Path
from getpass import getpass
from neo4j import GraphDatabase
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent

# 1. Đọc embedding và index
embeddings = np.load(
    BASE_DIR / "nlp" / "paper_embeddings.npy",
    allow_pickle=False
)

index_df = pd.read_csv(
    BASE_DIR / "nlp" / "embedding_index.csv",
    dtype={"paper_id": str}
)

print("Embedding shape:", embeddings.shape)
print("Index records:", len(index_df))

# 2. Kiểm tra tính nhất quán
assert embeddings.shape == (1497, 384)
assert len(index_df) == len(embeddings)
assert index_df["paper_id"].is_unique
assert index_df["row_index"].is_unique
assert np.isfinite(embeddings).all()

assert set(index_df["row_index"]) == set(
    range(len(embeddings))
)

# 3. Ánh xạ Paper ID với vector
records = []

for row in index_df.itertuples(index=False):
    records.append({
        "paper_id": row.paper_id,
        "embedding": embeddings[
            int(row.row_index)
        ].astype(float).tolist()
    })

# 4. Kết nối Neo4j
URI = "neo4j://127.0.0.1:7687"
PASSWORD = getpass("Neo4j password: ")

driver = GraphDatabase.driver(
    URI,
    auth=("neo4j", PASSWORD)
)

QUERY = """
UNWIND $rows AS row
MATCH (p:Paper {paper_id: row.paper_id})
SET p.embedding = row.embedding
RETURN count(p) AS updated
"""

def import_batch(tx, rows):
    return tx.run(
        QUERY, rows=rows
    ).single()["updated"]

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:
        paper_ids = set(
            session.run(
                "MATCH (p:Paper) RETURN p.paper_id AS id"
            ).value("id")
        )

        missing = set(index_df["paper_id"]) - paper_ids
        assert not missing, f"Missing Paper IDs: {len(missing)}"

        total_updated = 0
        batch_size = 100

        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]

            updated = session.execute_write(
                import_batch, batch
            )

            total_updated += updated

            print(
                f"Updated {total_updated}/{len(records)}"
            )

    print("Embedding import completed!")

finally:
    driver.close()
