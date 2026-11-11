
/*
Graph Data Science
PageRank, Louvain, WCC, Degree Centrality
*/

-- 1. Citation graph projection
CALL gds.graph.project(
    'citationGraph',
    'Paper',
    'CITES'
);

-- 2. PageRank
CALL gds.pageRank.write('citationGraph', {
    maxIterations: 20,
    dampingFactor: 0.85,
    writeProperty: 'citation_pagerank'
});

-- 3. Author collaboration graph projection
CALL gds.graph.project(
    'authorGraph',
    'Author',
    {
        CO_AUTHORED_WITH: {
            orientation: 'UNDIRECTED'
        }
    }
);

-- 4. Louvain
CALL gds.louvain.write('authorGraph', {
    writeProperty: 'community_id'
});

-- 5. WCC
CALL gds.wcc.write('authorGraph', {
    writeProperty: 'component_id'
});

-- 6. Degree Centrality
CALL gds.degree.write('authorGraph', {
    writeProperty: 'collaboration_degree'
});

-- 7. Clustering Coefficient
CALL gds.localClusteringCoefficient.stats(
    'authorGraph'
);
