
from pathlib import Path
from getpass import getpass
from neo4j import GraphDatabase
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

FILE_PATH = BASE_DIR / "nlp" / "topic_predictions.csv"

# 1. Đọc dữ liệu
df = pd.read_csv(FILE_PATH, dtype={"paper_id": str})

print("Total predictions:", len(df))
print("Unique Paper IDs:", df["paper_id"].nunique())

assert df["paper_id"].notna().all()
assert not df["paper_id"].duplicated().any()

# 2. Chuẩn bị thuộc tính NLP
columns = [
    "paper_id",
    "top1_topic",
    "top2_topic",
    "top1_score",
    "top2_score",
    "primary_score",
    "primary_rank",
    "model"
]

data = df[columns].copy()

for col in ["top1_score", "top2_score", "primary_score"]:
    data[col] = pd.to_numeric(data[col], errors="coerce")

data["primary_rank"] = pd.to_numeric(
    data["primary_rank"], errors="coerce"
)

data = data.astype(object).where(
    pd.notna(data), None
)

records = data.to_dict("records")

# 3. Kết nối Neo4j
URI = "neo4j://127.0.0.1:7687"
PASSWORD = getpass("Neo4j password: ")

driver = GraphDatabase.driver(
    URI,
    auth=("neo4j", PASSWORD)
)

QUERY = """
UNWIND $rows AS row
MATCH (p:Paper {paper_id: row.paper_id})

SET p.nlp_top1_topic = row.top1_topic,
    p.nlp_top2_topic = row.top2_topic,
    p.nlp_top1_score = row.top1_score,
    p.nlp_top2_score = row.top2_score,
    p.nlp_primary_score = row.primary_score,
    p.nlp_primary_rank = toInteger(row.primary_rank),
    p.nlp_model = row.model

RETURN count(p) AS updated
"""

def import_batch(tx, rows):
    return tx.run(QUERY, rows=rows).single()["updated"]

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:
        # Kiểm tra các Paper ID có tồn tại
        paper_ids = set(
            session.run(
                "MATCH (p:Paper) RETURN p.paper_id AS id"
            ).value("id")
        )

        missing_ids = set(df["paper_id"]) - paper_ids

        print("Missing Paper IDs:", len(missing_ids))

        if missing_ids:
            raise ValueError(
                f"Found {len(missing_ids)} missing Paper IDs"
            )

        total_updated = 0

        for start in range(0, len(records), 500):
            batch = records[start:start + 500]

            updated = session.execute_write(
                import_batch, batch
            )

            total_updated += updated

            print(
                f"Updated {total_updated}/{len(records)} papers"
            )

    print("NLP predictions imported successfully!")

finally:
    driver.close()
