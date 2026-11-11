# Manual audit of semantic candidate edges

- Uniform random sample size: **200**
- Labeled RELATED: **182**
- Labeled NOT_RELATED: **9**
- Labeled SAME_WORK: **1** (invalid as an edge between distinct works)
- UNCERTAIN: **8**
- Unlabeled: **0**
- Review complete: **NO**

- Preliminary precision among resolved sample: **94.79%**
- Wilson 95% CI on resolved sample: **90.68% to 97.15%**

**Important:** This estimates candidate-edge precision only for uniformly sampled edges under the current cosine/top-k settings. It does not estimate recall, generalization to new corpora, topic-classifier accuracy, or full graph accuracy. Do not claim final precision when review is incomplete.
