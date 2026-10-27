"""Train & compare sentiment models:
  TF-IDF + Logistic Regression, TF-IDF + Naive Bayes,  LSTM,  Bi-LSTM,  GRU.
Also produces the EDA plots (word frequency before/after stop-word removal)
and a confusion matrix.  Outputs go to models/ and reports/."""
import argparse
import os, sys, json, pickle
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import preprocess, tokenize, remove_stopwords

ROOT = Path(__file__).resolve().parent.parent
MODELS, REPORTS = ROOT / "models", ROOT / "reports"
LABELS = ["negative", "neutral", "positive"]
L2I = {l: i for i, l in enumerate(LABELS)}
MAXLEN, VOCAB, EMB = 40, 5000, 64
tf.random.set_seed(0); np.random.seed(0)


def eda(df):
    raw = Counter(w for t in df.text for w in tokenize(t))
    nostop = Counter(w for t in df.text for w in remove_stopwords(tokenize(t)))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for a, c, title in ((ax[0], raw, "Top words - original"), (ax[1], nostop, "Top words - stop words removed")):
        w, n = zip(*c.most_common(12))
        a.barh(w[::-1], n[::-1], color="#4f6bed"); a.set_title(title)
    plt.tight_layout(); plt.savefig(REPORTS / "word_frequency.png", dpi=130); plt.close()
    print(f"Vocabulary: original={len(raw)}  after stop-word removal={len(nostop)}")
    df.sentiment.value_counts().plot.bar(color=["#d9534f", "#999", "#3c9d5d"], title="Class distribution")
    plt.tight_layout(); plt.savefig(REPORTS / "class_distribution.png", dpi=130); plt.close()


def build_rnn(kind: str):
    m = models.Sequential([layers.Input(shape=(MAXLEN,)), layers.Embedding(VOCAB, EMB)])
    if kind == "lstm":
        m.add(layers.LSTM(64))
    elif kind == "bilstm":
        m.add(layers.Bidirectional(layers.LSTM(64)))
    elif kind == "gru":
        m.add(layers.GRU(64))
    m.add(layers.Dropout(0.4))
    m.add(layers.Dense(32, activation="relu"))
    m.add(layers.Dense(3, activation="softmax"))
    m.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data" / "reviews.csv",
        help="CSV with text and sentiment columns (default: data/reviews.csv).",
    )
    args = parser.parse_args()
    MODELS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
    df = pd.read_csv(args.data).dropna(subset=["text", "sentiment"])
    df = df[df.sentiment.isin(LABELS)].reset_index(drop=True)
    eda(df)
    df["clean"] = df.text.apply(preprocess)
    y = df.sentiment.map(L2I).values
    Xtr, Xte, ytr, yte = train_test_split(df.clean, y, test_size=0.2, stratify=y, random_state=42)
    results = {}

    # ---- Bag-of-Words + TF-IDF baselines ----
    print("BoW matrix shape:", CountVectorizer().fit_transform(Xtr).shape)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    Ttr, Tte = tfidf.fit_transform(Xtr), tfidf.transform(Xte)
    for name, clf in (("TF-IDF + Logistic Regression", LogisticRegression(max_iter=1000)),
                      ("TF-IDF + Naive Bayes", MultinomialNB())):
        clf.fit(Ttr, ytr); p = clf.predict(Tte)
        results[name] = (accuracy_score(yte, p), f1_score(yte, p, average="macro"))
        if "Logistic" in name:
            pickle.dump((tfidf, clf), open(MODELS / "tfidf_lr.pkl", "wb"))

    # ---- Deep models ----
    tok = Tokenizer(num_words=VOCAB, oov_token="<unk>"); tok.fit_on_texts(Xtr)
    Str = pad_sequences(tok.texts_to_sequences(Xtr), maxlen=MAXLEN)
    Ste = pad_sequences(tok.texts_to_sequences(Xte), maxlen=MAXLEN)
    pickle.dump(tok, open(MODELS / "sentiment_tokenizer.pkl", "wb"))
    best, best_acc, hist = None, 0, {}
    for kind, name in (("lstm", "LSTM"), ("bilstm", "Bi-LSTM"), ("gru", "GRU")):
        m = build_rnn(kind)
        h = m.fit(Str, ytr, validation_split=0.15, epochs=12, batch_size=64, verbose=0,
                  callbacks=[callbacks.EarlyStopping(patience=3, restore_best_weights=True)])
        p = m.predict(Ste, verbose=0).argmax(1)
        acc, f1 = accuracy_score(yte, p), f1_score(yte, p, average="macro")
        results[name] = (acc, f1); hist[name] = h.history
        print(f"{name}: acc={acc:.3f} f1={f1:.3f}  epochs={len(h.history['loss'])}")
        if kind == "lstm":  # the syllabus model is the one deployed in the app
            m.save(MODELS / "sentiment_lstm.keras"); best, best_pred = name, p
    # ---- Reports ----
    print("\n=== MODEL COMPARISON ===")
    tbl = pd.DataFrame(results, index=["Accuracy", "Macro-F1"]).T.round(4)
    print(tbl.to_string()); tbl.to_csv(REPORTS / "model_comparison.csv")
    tbl["Accuracy"].plot.barh(color="#4f6bed", title="Test accuracy by model", xlim=(0, 1))
    plt.tight_layout(); plt.savefig(REPORTS / "model_comparison.png", dpi=130); plt.close()
    for name, h in hist.items():
        plt.plot(h["val_accuracy"], label=name)
    plt.title("Validation accuracy per epoch"); plt.xlabel("epoch"); plt.legend()
    plt.tight_layout(); plt.savefig(REPORTS / "training_curves.png", dpi=130); plt.close()
    cm = confusion_matrix(yte, best_pred)
    plt.imshow(cm, cmap="Blues"); plt.xticks(range(3), LABELS); plt.yticks(range(3), LABELS)
    for i in range(3):
        for j in range(3):
            plt.text(j, i, cm[i, j], ha="center", va="center")
    plt.title("LSTM confusion matrix"); plt.xlabel("Predicted"); plt.ylabel("Actual")
    plt.tight_layout(); plt.savefig(REPORTS / "confusion_matrix.png", dpi=130); plt.close()
    print("\n", classification_report(yte, best_pred, target_names=LABELS))
    json.dump({k: {"accuracy": v[0], "f1": v[1]} for k, v in results.items()},
              open(REPORTS / "metrics.json", "w"), indent=2)


if __name__ == "__main__":
    main()
