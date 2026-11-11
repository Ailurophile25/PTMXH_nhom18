# Initial NLP evaluation (NOT independent graph accuracy)

Rule: model predicts the *original collection primary group* is relevant if it is among top 2 of 6 semantic topic scores. No tuning using these labels.
Samples joined to current corpus: **180**.
Human labels: positive=175, negative=5.
Confusion matrix: TP=170, FP=4, TN=1, FN=5.
Accuracy of the rule: **0.9500**.
Always-positive baseline accuracy on these labels: **0.9722**.
Precision (positive class): **0.9770**.
Recall (positive class): **0.9714**.
F1 (positive class): **0.9742**.
Precision (negative class): **0.1667**.
F1 (negative class): **0.1818**.

**LIMITATIONS:** Only the initial primary-group relevance was annotated, not a six-label ground truth. The existing sample is severely skewed toward positives, and evaluation must not be presented as >90% NLP or graph accuracy. Similarity scores are not probabilities, and this is a zero-shot baseline rather than a trained classifier.
