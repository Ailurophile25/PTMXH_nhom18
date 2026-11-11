
/*
Academic Research Graph
Network analysis queries
*/

-- 1. Top tác giả có nhiều bài báo
MATCH (a:Author)-[:AUTHORED]->(p:Paper)
RETURN a.name AS author,
       count(DISTINCT p) AS paper_count
ORDER BY paper_count DESC
LIMIT 20;

-- 2. Top tác giả theo Degree Centrality
MATCH (a:Author)
RETURN a.name AS author,
       a.collaboration_degree AS degree
ORDER BY degree DESC
LIMIT 20;

-- 3. Top Paper theo PageRank
MATCH (p:Paper)
RETURN p.title AS title,
       p.citation_pagerank AS pagerank,
       p.citation_count AS citations
ORDER BY pagerank DESC
LIMIT 20;

-- 4. Kích thước cộng đồng Louvain
MATCH (a:Author)
RETURN a.community_id AS community_id,
       count(*) AS author_count
ORDER BY author_count DESC
LIMIT 20;

-- 5. Kích thước thành phần liên thông
MATCH (a:Author)
RETURN a.component_id AS component_id,
       count(*) AS author_count
ORDER BY author_count DESC
LIMIT 20;

-- 6. Phân phối Degree
MATCH (a:Author)
RETURN a.collaboration_degree AS degree,
       count(*) AS author_count
ORDER BY degree;

-- 7. Phân bố chủ đề NLP
MATCH (p:Paper)
RETURN p.nlp_top1_topic AS topic,
       count(*) AS paper_count
ORDER BY paper_count DESC;

-- 8. Mật độ mạng cộng tác
MATCH (a:Author)
WITH count(a) AS N
MATCH (:Author)-[r:CO_AUTHORED_WITH]->(:Author)
WITH N, count(r) AS E
RETURN N, E,
       2.0 * E / (N * (N - 1)) AS density;
