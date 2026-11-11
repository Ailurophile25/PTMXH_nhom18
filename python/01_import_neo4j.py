
from neo4j import GraphDatabase
from getpass import getpass
from pathlib import Path
import pandas as pd

# 1. Kết nối Neo4j
URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = getpass("Enter Neo4j password: ")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# 2. Đọc dữ liệu Paper
BASE_DIR = Path(__file__).resolve().parent

FILE_PATH = BASE_DIR / "graph" / "processed" / "all_papers.csv"

papers_df = pd.read_csv(
    FILE_PATH,
    dtype={"paper_id": str, "venue_id": str}
)

print("Total papers:", len(papers_df))
print("Unique IDs:", papers_df["paper_id"].nunique())

# 3. Chọn các thuộc tính cần import
columns = [
    "paper_id",
    "title",
    "year",
    "abstract",
    "doi",
    "venue_id",
    "citation_count",
    "primary_group"
]

paper_data = papers_df[columns].copy()

paper_data = paper_data.dropna(subset=["paper_id"])
paper_data = paper_data.drop_duplicates(subset=["paper_id"])

# Chuyển NaN thành None để Neo4j xử lý được
paper_data = paper_data.astype(object).where(
    pd.notna(paper_data), None
)

for col in ["year", "citation_count"]:
    paper_data[col] = paper_data[col].apply(
        lambda x: int(x) if x is not None else None
    )

records = paper_data.to_dict("records")

# 4. Cypher import
QUERY = """
UNWIND $rows AS row
MERGE (p:Paper {paper_id: row.paper_id})
SET p.title = row.title,
    p.year = row.year,
    p.abstract = row.abstract,
    p.doi = row.doi,
    p.venue_id = row.venue_id,
    p.citation_count = row.citation_count,
    p.primary_group = row.primary_group
"""

def import_batch(tx, batch):
    tx.run(QUERY, rows=batch).consume()

# 5. Import theo batch
BATCH_SIZE = 500

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]

            session.execute_write(import_batch, batch)

            print(
                f"Imported {min(i + BATCH_SIZE, len(records))}"
                f"/{len(records)} papers"
            )

    print("Paper import completed!")

finally:
    driver.close()



# ===== IMPORT 4 NODE TYPES =====

NODE_CONFIGS = {
    "Author": {
        "file": "authors.csv",
        "id": "author_id",
        "columns": [
            "author_id", "name", "orcid",
            "normalized_name", "orcid_normalized"
        ]
    },
    "Institution": {
        "file": "institutions.csv",
        "id": "institution_id",
        "columns": [
            "institution_id", "name", "ror",
            "country_code", "normalized_name",
            "ror_normalized"
        ]
    },
    "Topic": {
        "file": "topics.csv",
        "id": "topic_id",
        "columns": ["topic_id", "name"]
    },
    "Venue": {
        "file": "venues.csv",
        "id": "venue_id",
        "columns": ["venue_id", "name", "type"]
    }
}

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:

        for label, config in NODE_CONFIGS.items():
            file_path = (
                BASE_DIR / "graph" / "processed"
                / config["file"]
            )

            df = pd.read_csv(file_path, dtype=str)

            id_col = config["id"]

            df = df.dropna(subset=[id_col])
            df = df.drop_duplicates(subset=[id_col])

            df = df[config["columns"]]
            df = df.astype(object).where(
                pd.notna(df), None
            )

            records = df.to_dict("records")

            query = f"""
            UNWIND $rows AS row
            MERGE (n:{label} {{{id_col}: row.{id_col}}})
            SET n += row
            """

            for i in range(0, len(records), 500):
                batch = records[i:i + 500]

                session.execute_write(
                    lambda tx, q, rows:
                        tx.run(q, rows=rows).consume(),
                    query,
                    batch
                )

            print(f"{label}: {len(records)} imported")

finally:
    driver.close()

print("All node imports completed!")


# ===== IMPORT WRITES RELATIONSHIPS =====

file_path = (
    BASE_DIR / "graph" / "processed" / "authorships.csv"
)

writes_df = pd.read_csv(file_path, dtype=str)

writes_df = writes_df.dropna(
    subset=["paper_id", "author_id"]
)

writes_df = writes_df.drop_duplicates(
    subset=["paper_id", "author_id"]
)

records = writes_df[
    ["paper_id", "author_id", "author_order"]
].astype(object).where(
    pd.notna(writes_df[
        ["paper_id", "author_id", "author_order"]
    ]), None
).to_dict("records")

QUERY_WRITES = """
UNWIND $rows AS row

MATCH (a:Author {author_id: row.author_id})
MATCH (p:Paper {paper_id: row.paper_id})

MERGE (a)-[r:AUTHORED]->(p)

SET r.author_order =
    CASE
        WHEN row.author_order IS NULL THEN NULL
        ELSE toInteger(row.author_order)
    END
"""

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    with driver.session(database="neo4j") as session:
        for i in range(0, len(records), 500):
            batch = records[i:i + 500]

            session.execute_write(
                lambda tx, rows:
                    tx.run(
                        QUERY_WRITES,
                        rows=rows
                    ).consume(),
                batch
            )

        print("WRITES imported:", len(records))

finally:
    driver.close()


# ===== IMPORT HAS_TOPIC RELATIONSHIPS =====

file_path = (
    BASE_DIR / "graph" / "processed" / "paper_topics.csv"
)

topics_df = pd.read_csv(file_path, dtype=str)

topics_df = topics_df.dropna(
    subset=["paper_id", "topic_id"]
)

topics_df = topics_df.drop_duplicates(
    subset=["paper_id", "topic_id"]
)

topics_df["score"] = pd.to_numeric(
    topics_df["score"],
    errors="coerce"
)

records = topics_df.astype(object).where(
    pd.notna(topics_df), None
).to_dict("records")

QUERY_HAS_TOPIC = """
UNWIND $rows AS row

MATCH (p:Paper {paper_id: row.paper_id})
MATCH (t:Topic {topic_id: row.topic_id})

MERGE (p)-[r:HAS_TOPIC]->(t)

SET r.score = row.score
"""

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    with driver.session(database="neo4j") as session:
        for i in range(0, len(records), 500):
            batch = records[i:i + 500]

            session.execute_write(
                lambda tx, rows:
                    tx.run(
                        QUERY_HAS_TOPIC,
                        rows=rows
                    ).consume(),
                batch
            )

    print("HAS_TOPIC imported:", len(records))

finally:
    driver.close()

# ===== IMPORT AFFILIATED_WITH =====

file_path = (
    BASE_DIR / "graph" / "processed"
    / "author_institutions.csv"
)

aff_df = pd.read_csv(file_path, dtype=str)

aff_df = aff_df.dropna(
    subset=["author_id", "institution_id"]
)

# Gộp các bản ghi cùng Author - Institution
aff_grouped = (
    aff_df.groupby(
        ["author_id", "institution_id"],
        as_index=False
    )
    .agg(
        record_count=("paper_id", "size"),
        paper_count=("paper_id", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max")
    )
)

aff_grouped["first_year"] = (
    aff_grouped["first_year"].astype(int)
)
aff_grouped["last_year"] = (
    aff_grouped["last_year"].astype(int)
)

records = aff_grouped.to_dict("records")

print("Original records:", len(aff_df))
print("Unique relationships:", len(records))

QUERY_AFFILIATION = """
UNWIND $rows AS row

MATCH (a:Author {author_id: row.author_id})
MATCH (i:Institution {institution_id: row.institution_id})

MERGE (a)-[r:AFFILIATED_WITH]->(i)

SET r.record_count = row.record_count,
    r.paper_count = row.paper_count,
    r.first_year = row.first_year,
    r.last_year = row.last_year
"""

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    with driver.session(database="neo4j") as session:
        for start in range(0, len(records), 500):
            batch = records[start:start + 500]

            session.execute_write(
                lambda tx, rows:
                    tx.run(
                        QUERY_AFFILIATION,
                        rows=rows
                    ).consume(),
                batch
            )

    print("AFFILIATED_WITH import completed!")

finally:
    driver.close()


# ===== IMPORT PUBLISHED_IN =====

file_path = (
    BASE_DIR / "graph" / "processed" / "all_papers.csv"
)

venue_df = pd.read_csv(file_path, dtype=str)

venue_df = venue_df.dropna(
    subset=["paper_id", "venue_id"]
)

venue_df = venue_df.drop_duplicates(
    subset=["paper_id", "venue_id"]
)

records = venue_df[
    ["paper_id", "venue_id"]
].to_dict("records")

QUERY_PUBLISHED_IN = """
UNWIND $rows AS row

MATCH (p:Paper {paper_id: row.paper_id})
MATCH (v:Venue {venue_id: row.venue_id})

MERGE (p)-[:PUBLISHED_IN]->(v)
"""

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    with driver.session(database="neo4j") as session:
        for start in range(0, len(records), 500):
            batch = records[start:start + 500]

            session.execute_write(
                lambda tx, rows:
                    tx.run(
                        QUERY_PUBLISHED_IN,
                        rows=rows
                    ).consume(),
                batch
            )

    print("Candidate PUBLISHED_IN records:", len(records))
    print("Import completed!")

finally:
    driver.close()


# ===== INSPECT CITATION DATA =====

citation_path = (
    BASE_DIR / "graph" / "processed" / "references.csv"
)

citations_df = pd.read_csv(citation_path, dtype=str)


# ===== IMPORT CITES =====

# Chỉ lấy citation giữa các Paper trong corpus
internal_citations = citations_df[
    citations_df["in_sample"] == "1"
].copy()

# Kiểm tra cả hai ID có trong corpus
paper_ids = set(papers_df["paper_id"].dropna())

internal_citations = internal_citations[
    internal_citations["citing_paper_id"].isin(paper_ids)
    & internal_citations["cited_paper_id"].isin(paper_ids)
]

# Xóa cặp citation trùng
internal_citations = internal_citations.drop_duplicates(
    subset=["citing_paper_id", "cited_paper_id"]
)

records = internal_citations[
    ["citing_paper_id", "cited_paper_id"]
].to_dict("records")

print("CITES ready to import:", len(records))

QUERY_CITES = """
UNWIND $rows AS row

MATCH (p1:Paper {paper_id: row.citing_paper_id})
MATCH (p2:Paper {paper_id: row.cited_paper_id})

MERGE (p1)-[:CITES]->(p2)
"""

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    with driver.session(database="neo4j") as session:
        for start in range(0, len(records), 500):
            batch = records[start:start + 500]

            session.execute_write(
                lambda tx, rows:
                    tx.run(QUERY_CITES, rows=rows).consume(),
                batch
            )

    print("CITES import completed!")

finally:
    driver.close()
