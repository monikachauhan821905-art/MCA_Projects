"""TF-IDF keyword extraction + aspect-wise insights for course reviews."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import preprocess

ASPECT_WORDS = {
    "Teaching": {"teacher", "professor", "faculty", "instructor", "lecturer", "lecture"},
    "Content": {"syllabus", "content", "material", "topic", "curriculum"},
    "Assignments": {"assignment", "homework", "project", "task"},
    "Exams": {"exam", "test", "quiz", "evaluation"},
    "Labs": {"lab", "practical", "hand"},
    "Pace": {"pace", "speed", "schedule", "rushed", "fast", "slow"},
    "Support": {"doubt", "support", "mentoring", "feedback"},
    "Resources": {"slide", "note", "video", "resource"},
}


def top_keywords(texts, n=10, ngram=(1, 2)):
    """Rank terms across a set of reviews by summed TF-IDF weight."""
    docs = [preprocess(t) for t in texts if str(t).strip()]
    if not docs:
        return []
    vec = TfidfVectorizer(ngram_range=ngram, min_df=1, sublinear_tf=True)
    M = vec.fit_transform(docs)
    scores = np.asarray(M.sum(axis=0)).ravel()
    terms = np.array(vec.get_feature_names_out())
    idx = scores.argsort()[::-1][:n]
    return list(zip(terms[idx], scores[idx].round(3)))


def aspect_breakdown(texts, predict_fn):
    """For each review sentence that mentions an aspect, predict its sentiment.
    predict_fn(list[str]) -> list[str] labels.  Returns a DataFrame."""
    rows = []
    for t in texts:
        for s in str(t).replace("!", ".").split("."):
            if len(s.split()) < 3:
                continue
            toks = set(preprocess(s).split())
            for asp, words in ASPECT_WORDS.items():
                if toks & words:
                    rows.append((asp, s.strip()))
    if not rows:
        return pd.DataFrame(columns=["Aspect", "positive", "neutral", "negative"])
    df = pd.DataFrame(rows, columns=["Aspect", "sentence"])
    df["sentiment"] = predict_fn(df.sentence.tolist())
    tab = df.groupby(["Aspect", "sentiment"]).size().unstack(fill_value=0)
    for c in ("positive", "neutral", "negative"):
        if c not in tab:
            tab[c] = 0
    tab = tab[["positive", "neutral", "negative"]]
    tab["score"] = ((tab.positive - tab.negative) / tab.sum(axis=1)).round(2)
    return tab.sort_values("score").reset_index()
