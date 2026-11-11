
/*
Academic Research Graph
Graph validation queries
Database: neo4j
*/

-- 1. Tổng số node
MATCH (n)
RETURN count(n) AS total_nodes;

-- 2. Số node theo từng loại
MATCH (n)
UNWIND labels(n) AS node_type
RETURN node_type, count(*) AS total
ORDER BY node_type;

-- 3. Tổng số cạnh
MATCH ()-[r]->()
RETURN count(r) AS total_relationships;

-- 4. Số cạnh theo từng loại
MATCH ()-[r]->()
RETURN type(r) AS relationship_type,
       count(r) AS total
ORDER BY relationship_type;

-- 5. Kiểm tra Paper có NLP predictions
MATCH (p:Paper)
RETURN count(p) AS total_papers,
       count(p.nlp_top1_topic) AS with_predictions,
       count(p.embedding) AS with_embeddings;

-- 6. Kiểm tra chiều embedding
MATCH (p:Paper)
WHERE p.embedding IS NOT NULL
RETURN min(size(p.embedding)) AS min_dimensions,
       max(size(p.embedding)) AS max_dimensions;

-- 7. Kiểm tra ràng buộc ID
SHOW CONSTRAINTS;
