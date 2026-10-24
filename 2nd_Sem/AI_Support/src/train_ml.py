import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# load dataset
df = pd.read_csv("data/dataset.csv")

X = df["query"]
y = df["intent"]

# vectorizer
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

# model
model = MultinomialNB()
model.fit(X_vec, y)

# save model + vectorizer
pickle.dump(model, open("models/model.pkl", "wb"))
pickle.dump(vectorizer, open("models/vectorizer.pkl", "wb"))

print("✅ Model trained and saved successfully!")