"""Prepare a balanced sentiment CSV from public RateMyProfessors ratings.

The source contains scraped reviews and original 1-5 ratings. This script
keeps only integer ratings so sentiment labels are derived transparently:
1-2 negative, 3 neutral, and 4-5 positive. Decimal ratings are excluded.
"""
import argparse
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = (
    "https://huggingface.co/datasets/Z-H-Che/ratemyprofessors_reviews/"
    "resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
LABELS = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--per-class",
        type=int,
        default=3000,
        help="Maximum number of reviews per sentiment class (default: 3000).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "reviews_public.csv",
        help="Output CSV path (default: data/reviews_public.csv).",
    )
    args = parser.parse_args()
    if args.per_class < 1:
        parser.error("--per-class must be at least 1")

    print("Downloading public review ratings...")
    with urlopen(SOURCE_URL, timeout=120) as response:
        raw_data = response.read()

    reviews = pd.read_parquet(BytesIO(raw_data), columns=["text", "rating"])
    reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
    reviews = reviews.dropna(subset=["text", "rating"])
    reviews["text"] = reviews["text"].astype(str).str.strip()
    reviews = reviews[reviews["text"].str.len() > 0]
    reviews = reviews[reviews["rating"].isin(LABELS)]
    reviews["sentiment"] = reviews["rating"].astype(int).map(LABELS)
    reviews = reviews.drop_duplicates(subset=["text"])

    counts = reviews["sentiment"].value_counts()
    if not all(label in counts for label in LABELS.values()):
        raise ValueError(f"Source did not provide every sentiment class: {counts.to_dict()}")

    sample = pd.concat(
        [
            group.sample(n=min(args.per_class, len(group)), random_state=42)
            for _, group in reviews.groupby("sentiment")
        ],
        ignore_index=True,
    )
    sample = sample[["text", "sentiment"]].sample(frac=1, random_state=42)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False)

    print(f"Saved {len(sample):,} reviews to {args.output}")
    print(sample["sentiment"].value_counts().sort_index().to_string())
    print(f"Excluded non-integer and invalid ratings; mapping: {LABELS}")


if __name__ == "__main__":
    main()
