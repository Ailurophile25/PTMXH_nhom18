
from pathlib import Path
from getpass import getpass
from neo4j import GraphDatabase
import pandas as pd
import json

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "graph" / "derived_edges.csv"

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = getpass("Neo4j password: ")

# Chỉ cho phép 5 loại quan hệ đã xác định
RELATIONSHIPS = {
    "CO_AUTHORED_WITH": ("Author", "author_id", "Author", "author_id"),
    "RESEARCHES": ("Author", "author_id", "Topic", "topic_id"),
    "COLLABORATES_WITH": (
        "Institution", "institution_id",
        "Institution", "institution_id"
    ),
    "BIBLIOGRAPHIC_COUPLING": (
        "Paper", "paper_id", "Paper", "paper_id"
    ),
    "CO_CITED_WITH": ("Paper", "paper_id", "Paper", "paper_id")
}

# Đọc dữ liệu
df = pd.read_csv(FILE_PATH, dtype=str)

print("Original derived records:", len(df))
print(df["relationship_type"].value_counts())

# Kiểm tra dữ liệu trước khi import
assert len(df) == 32948
assert df["relationship_type"].isin(RELATIONSHIPS).all()
assert not df[
    ["relationship_type", "source_id", "target_id"]
].isna().any().any()

df = df.drop_duplicates(
    subset=["relationship_type", "source_id", "target_id"]
)

df["weight"] = pd.to_numeric(df["weight"], errors="raise")
df["evidence_count"] = pd.to_numeric(
    df["evidence_count"], errors="raise"
).astype(int)

df["evidence_ids"] = df["evidence_ids"].apply(json.loads)

assert df["evidence_ids"].apply(
    lambda x: isinstance(x, list)
).all()

driver = GraphDatabase.driver(
    URI, auth=(USERNAME, PASSWORD)
)

def run_import(tx, query, rows):
    tx.run(query, rows=rows).consume()

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:

        # Không import nếu số node chưa đúng
        node_count = session.run(
            "MATCH (n) RETURN count(n) AS total"
        ).single()["total"]

        assert node_count == 8452, (
            f"Unexpected node count: {node_count}"
        )

        for rel_type, config in RELATIONSHIPS.items():
            source_label, source_key, target_label, target_key = config

            subset = df[df["relationship_type"] == rel_type].copy()
            records = subset.to_dict("records")

            # Kiểm tra cả hai endpoint đã có
            check_query = f"""
            UNWIND $rows AS row
            OPTIONAL MATCH (s:{source_label}
                {{{source_key}: row.source_id}})
            OPTIONAL MATCH (t:{target_label}
                {{{target_key}: row.target_id}})
            RETURN count(*) AS checked,
                   count(s) AS sources_found,
                   count(t) AS targets_found
            """

            for start in range(0, len(records), 500):
                batch = records[start:start + 500]
                result = session.run(
                    check_query, rows=batch
                ).single()

                if (result["sources_found"] != len(batch)
                        or result["targets_found"] != len(batch)):
                    raise ValueError(
                        f"Missing endpoints in {rel_type}"
                    )

            # MATCH: không tạo thêm node
            query = f"""
            UNWIND $rows AS row
            MATCH (s:{source_label}
                {{{source_key}: row.source_id}})
            MATCH (t:{target_label}
                {{{target_key}: row.target_id}})
            MERGE (s)-[r:{rel_type}]->(t)
            SET r.weight = toFloat(row.weight),
                r.evidence_count = row.evidence_count,
                r.evidence_ids = row.evidence_ids,
                r.metric = row.metric
            """

            for start in range(0, len(records), 500):
                batch = records[start:start + 500]
                session.execute_write(run_import, query, batch)

            actual = session.run(
                f"MATCH ()-[r:{rel_type}]->() "
                "RETURN count(r) AS total"
            ).single()["total"]

            print(f"{rel_type}: {actual}/{len(records)}")
            assert actual == len(records)

        print("Derived relationships imported successfully!")

finally:
    driver.close()
