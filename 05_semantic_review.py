
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
NLP_DIR = BASE_DIR / "nlp"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

candidates = pd.read_csv(
    NLP_DIR / "semantic_similarity_candidates.csv"
)

review = pd.read_csv(
    NLP_DIR / "semantic_review_sample_completed.csv"
)

print("Total candidates:", len(candidates))
print("Reviewed pairs:", len(review))

print("\nReview decisions:")
print(review["decision"].value_counts())

# Kiểm tra ID và các cặp được review
assert review["source_id"].notna().all()
assert review["target_id"].notna().all()

# Chuẩn hóa cặp Paper vì similarity là quan hệ đối xứng
def pair_key(df):
    return df.apply(
        lambda row: tuple(sorted([
            row["source_id"],
            row["target_id"]
        ])),
        axis=1
    )

candidates["pair_key"] = pair_key(candidates)
review["pair_key"] = pair_key(review)

print("\nDuplicate candidate pairs:",
      candidates["pair_key"].duplicated().sum())

print("Duplicate reviewed pairs:",
      review["pair_key"].duplicated().sum())

print("Reviewed pairs found in candidates:",
      review["pair_key"].isin(
          set(candidates["pair_key"])
      ).sum())

# Thống kê điểm similarity theo quyết định
summary = (
    review.groupby("decision")["cosine_similarity"]
    .agg(["count", "mean", "min", "max"])
    .reset_index()
)

print("\nSimilarity by decision:")
print(summary.to_string(index=False))

summary.to_csv(
    REPORT_DIR / "semantic_review_statistics.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nSaved semantic review statistics!")
