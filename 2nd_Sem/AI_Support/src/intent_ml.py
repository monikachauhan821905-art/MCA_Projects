import pickle

model = pickle.load(open("models/model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))

def predict_intent(text):
    X = vectorizer.transform([text])
    return model.predict(X)[0]