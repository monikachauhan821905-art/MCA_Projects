"""Generates a synthetic student course-review dataset (data/reviews.csv).

Kaggle could not be reached from the build environment, so this creates a
realistic, noisy stand-in: 3 classes (negative / neutral / positive), 8 aspects,
mixed-sentiment sentences, typos, and ~6% label noise so accuracy is not 100%.

TO USE REAL DATA: replace data/reviews.csv with any CSV that has the columns
`text` and `sentiment` (negative / neutral / positive). Nothing else changes.
"""
import random
import pandas as pd
from pathlib import Path

random.seed(42)

ASPECTS = {
    "teaching": ("the teacher", "the professor", "the faculty", "the instructor", "the lecturer"),
    "content": ("the syllabus", "the course content", "the study material", "the topics", "the curriculum"),
    "assignments": ("the assignments", "the homework", "the projects", "the practical tasks"),
    "exams": ("the exams", "the tests", "the quizzes", "the evaluation"),
    "lab": ("the lab sessions", "the practicals", "the lab work", "the hands-on sessions"),
    "pace": ("the pace of the course", "the speed of lectures", "the schedule"),
    "support": ("the doubt clearing", "the student support", "the mentoring", "the feedback on my work"),
    "slides": ("the slides", "the notes", "the lecture videos", "the online resources"),
}
POS = ["was excellent", "was very helpful", "was really well organized", "was engaging and clear",
       "was amazing", "made learning enjoyable", "was great and easy to follow", "exceeded my expectations",
       "was truly useful for my career", "was fantastic", "was well explained", "was very good"]
NEG = ["was terrible", "was very confusing", "was poorly organized", "was boring and unclear",
       "was a waste of time", "made learning difficult", "was far too rushed", "did not meet my expectations",
       "was not helpful at all", "was disappointing", "was badly explained", "was really bad"]
NEU = ["was okay", "was average", "was fine, nothing special", "was neither good nor bad",
       "was acceptable", "was as expected", "was decent but not memorable", "was just about alright"]
POS_OPEN = ["I loved this course.", "Overall a great experience.", "Highly recommended.", "Really enjoyed it.",
            "One of the best courses I have taken.", "I learned a lot.", ""]
NEG_OPEN = ["I regret taking this course.", "Overall a bad experience.", "I would not recommend it.",
            "Very disappointed.", "I learned almost nothing.", "Not worth the fees.", ""]
NEU_OPEN = ["The course was alright.", "It was an average semester.", "Nothing special overall.", "", ""]
POS_CLOSE = ["I would take another course from this department.", "Please keep it up!", "Five stars.", ""]
NEG_CLOSE = ["Please improve this next semester.", "Needs major changes.", "Total disappointment.", ""]
NEU_CLOSE = ["It did the job.", "Could be better, could be worse.", ""]


def typo(s: str) -> str:
    if random.random() < 0.12 and len(s) > 20:
        i = random.randrange(5, len(s) - 5)
        s = s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return s


def make_review(label: str) -> str:
    pool = {"positive": (POS, POS_OPEN, POS_CLOSE), "negative": (NEG, NEG_OPEN, NEG_CLOSE),
            "neutral": (NEU, NEU_OPEN, NEU_CLOSE)}
    main, openers, closers = pool[label]
    parts = [random.choice(openers)]
    for asp in random.sample(list(ASPECTS), k=random.choice([1, 2, 2, 3])):
        thing = random.choice(ASPECTS[asp])
        # 20% of sentences carry the opposite sentiment -> mixed reviews
        if label != "neutral" and random.random() < 0.20:
            other = NEG if label == "positive" else POS
            parts.append(f"{thing.capitalize()} {random.choice(other)}, though.")
        else:
            parts.append(f"{thing.capitalize()} {random.choice(main)}.")
    parts.append(random.choice(closers))
    text = " ".join(p for p in parts if p)
    return typo(text)


def main(n_per_class: int = 1000):
    rows = []
    for label in ("positive", "negative", "neutral"):
        for _ in range(n_per_class):
            rows.append((make_review(label), label))
    # ~6% label noise (real labels are never perfect)
    labels = ["positive", "negative", "neutral"]
    noisy = []
    for text, lab in rows:
        if random.random() < 0.06:
            lab = random.choice([l for l in labels if l != lab])
        noisy.append((text, lab))
    df = pd.DataFrame(noisy, columns=["text", "sentiment"]).sample(frac=1, random_state=1).reset_index(drop=True)
    out = Path(__file__).resolve().parent.parent / "data" / "reviews.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} reviews -> {out}")
    print(df.sentiment.value_counts().to_string())
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
