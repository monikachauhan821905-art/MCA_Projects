"""GRU next-word prediction (syllabus experiment: 'Build a model using GRU for
predicting next word').  Trained on the review text so it can auto-suggest
the next word while a student is typing feedback."""
import os, sys, pickle
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import light_clean

ROOT = Path(__file__).resolve().parent.parent
SEQ = 8  # context window (words)
tf.random.set_seed(0); np.random.seed(0)


def main():
    df = pd.read_csv(ROOT / "data" / "reviews.csv")
    sents = []
    for t in df.text:  # one training "sentence" per sentence of a review
        for s in str(t).replace("!", ".").split("."):
            s = light_clean(s)
            if len(s.split()) >= 3:
                sents.append(s)
    sents = list(dict.fromkeys(sents))  # de-duplicate
    tok = Tokenizer(); tok.fit_on_texts(sents)
    vocab = len(tok.word_index) + 1
    X, y = [], []
    for s in sents:
        ids = tok.texts_to_sequences([s])[0]
        for i in range(1, len(ids)):  # every prefix -> next word
            X.append(ids[max(0, i - SEQ):i]); y.append(ids[i])
    X = pad_sequences(X, maxlen=SEQ); y = np.array(y)
    print(f"{len(sents)} unique sentences, {len(X)} training pairs, vocab={vocab}")

    m = models.Sequential([layers.Input(shape=(SEQ,)), layers.Embedding(vocab, 64),
                           layers.GRU(128), layers.Dropout(0.2),
                           layers.Dense(vocab, activation="softmax")])
    m.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    m.fit(X, y, epochs=25, batch_size=128, validation_split=0.1, verbose=0)
    loss, acc = m.evaluate(X, y, verbose=0)
    print(f"next-word accuracy (train): {acc:.3f}")
    m.save(ROOT / "models" / "nextword_gru.keras")
    pickle.dump(tok, open(ROOT / "models" / "nextword_tokenizer.pkl", "wb"))
    for seed in ("the teacher was", "the exams were", "i would"):
        print(f"  '{seed}' ->", predict_next(m, tok, seed))


def predict_next(model, tok, text, k=3):
    ids = tok.texts_to_sequences([light_clean(text)])[0][-SEQ:]
    if not ids:
        return []
    p = model.predict(pad_sequences([ids], maxlen=SEQ), verbose=0)[0]
    inv = {v: k_ for k_, v in tok.word_index.items()}
    # skip rare words (typos in the data) so suggestions look clean
    ok = [inv[i] for i in np.argsort(p)[::-1] if i in inv and tok.word_counts.get(inv[i], 0) >= 5]
    return ok[:k]


if __name__ == "__main__":
    main()
