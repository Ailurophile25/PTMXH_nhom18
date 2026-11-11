
from pathlib import Path
from getpass import getpass
from neo4j import GraphDatabase
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "reports" / "neo4j_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URI = "neo4j://127.0.0.1:7687"
PASSWORD = getpass("Neo4j password: ")

driver = GraphDatabase.driver(
    URI,
    auth=("neo4j", PASSWORD)
)

QUERIES = {

    # 1. Thống kê các loại node
    "node_statistics": """
        MATCH (n)
        UNWIND labels(n) AS node_type
        RETURN node_type, count(*) AS total
        ORDER BY node_type
    """,

    # 2. Thống kê các loại quan hệ
    "relationship_statistics": """
        MATCH ()-[r]->()
        RETURN type(r) AS relationship_type,
               count(*) AS total
        ORDER BY relationship_type
    """,

    # 3. Top 20 tác giả theo số công trình
    "top_authors_by_papers": """
        MATCH (a:Author)-[:AUTHORED]->(p:Paper)
        RETURN a.author_id AS author_id,
               a.name AS author,
               count(DISTINCT p) AS paper_count
        ORDER BY paper_count DESC
        LIMIT 20
    """,

    # 4. Top 20 tác giả theo Degree Centrality
    "top_authors_by_degree": """
        MATCH (a:Author)
        RETURN a.author_id AS author_id,
               a.name AS author,
               a.collaboration_degree AS degree,
               a.community_id AS community_id,
               a.component_id AS component_id
        ORDER BY degree DESC
        LIMIT 20
    """,

    # 5. Top 20 Paper theo Citation PageRank
    "top_papers_by_pagerank": """
        MATCH (p:Paper)
        RETURN p.paper_id AS paper_id,
               p.title AS title,
               p.year AS year,
               p.citation_count AS citation_count,
               p.citation_pagerank AS pagerank
        ORDER BY pagerank DESC
        LIMIT 20
    """,

    # 6. Thống kê kích thước các cộng đồng Louvain
    "community_sizes": """
        MATCH (a:Author)
        WHERE a.community_id IS NOT NULL
        RETURN a.community_id AS community_id,
               count(*) AS author_count
        ORDER BY author_count DESC
    """,

    # 7. Thống kê WCC
    "component_sizes": """
        MATCH (a:Author)
        WHERE a.component_id IS NOT NULL
        RETURN a.component_id AS component_id,
               count(*) AS author_count
        ORDER BY author_count DESC
    """,

    # 8. Phân phối Degree
    "degree_distribution": """
        MATCH (a:Author)
        WHERE a.collaboration_degree IS NOT NULL
        RETURN toInteger(a.collaboration_degree) AS degree,
               count(*) AS author_count
        ORDER BY degree
    """,

    # 9. Thống kê các chủ đề NLP
    "nlp_topic_distribution": """
        MATCH (p:Paper)
        WHERE p.nlp_top1_topic IS NOT NULL
        RETURN p.nlp_top1_topic AS topic,
               count(*) AS paper_count,
               avg(p.nlp_top1_score) AS avg_similarity
        ORDER BY paper_count DESC
    """,

    # 10. Mật độ mạng cộng tác
    "network_density": """
        MATCH (a:Author)
        WITH count(a) AS N
        MATCH (:Author)-[r:CO_AUTHORED_WITH]->(:Author)
        WITH N, count(r) AS E
        RETURN N AS total_authors,
               E AS total_collaborations,
               2.0 * E / (N * (N - 1)) AS density
    """,

    # 11. Degree toàn mạng
    "degree_summary": """
        MATCH (a:Author)
        RETURN count(a) AS total_authors,
               avg(a.collaboration_degree) AS avg_degree,
               min(a.collaboration_degree) AS min_degree,
               max(a.collaboration_degree) AS max_degree,
               sum(
                   CASE WHEN a.collaboration_degree = 0
                   THEN 1 ELSE 0 END
               ) AS isolated_authors
    """,

    # 12. Clustering Coefficient
    "clustering_coefficient": """
        CALL gds.localClusteringCoefficient.stats(
            'authorGraph'
        )
        YIELD nodeCount, averageClusteringCoefficient
        RETURN nodeCount,
               averageClusteringCoefficient
    """,

    # 13. Louvain summary
    "louvain_summary": """
        CALL gds.louvain.stats('authorGraph')
        YIELD communityCount, modularity
        RETURN communityCount, modularity
    """,

    # 14. WCC summary
    "wcc_summary": """
        CALL gds.wcc.stats('authorGraph')
        YIELD componentCount, componentDistribution
        RETURN componentCount,
               componentDistribution
    """
}

try:
    driver.verify_connectivity()

    with driver.session(database="neo4j") as session:

        for name, query in QUERIES.items():
            print(f"Exporting {name}...")

            result = session.run(query)
            records = [dict(row) for row in result]

            df = pd.DataFrame(records)

            output_path = OUTPUT_DIR / f"{name}.csv"

            df.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig"
            )

            print(f"  Saved: {output_path.name} ({len(df)} rows)")

    print("\nAll analysis results exported successfully!")

finally:
    driver.close()
