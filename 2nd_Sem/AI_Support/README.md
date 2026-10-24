# 🤖 AI Customer Support Chatbot

An AI-powered customer support chatbot that combines **Machine Learning** and **Generative AI** to provide intelligent and interactive responses to user queries.

---

## 🚀 Features

* 💬 Real-time chatbot interface
* 🧠 Intent Classification using Machine Learning
* 🤖 Response Generation using rule-based + T5 model
* ⚡ Fast API backend using Flask
* 🎨 Interactive UI with typing animation
* 🔄 Handles multiple query types:

  * Greeting
  * Refund
  * Complaint
  * Inquiry
  * Technical Issues

---

## 🧠 How It Works

1. User enters a message in the chat UI
2. Message is sent to Flask backend (`/chat` API)
3. ML model classifies intent using:

   * TF-IDF Vectorizer
   * Naive Bayes Classifier
4. Based on intent, response is generated:

   * Rule-based replies (primary)
   * T5 model (fallback for natural responses)
5. Response is displayed in chat UI with typing animation

---

## 🛠️ Tech Stack

### 🔹 Backend

* Python
* Flask

### 🔹 Machine Learning

* scikit-learn
* Naive Bayes
* TF-IDF Vectorizer

### 🔹 Generative AI

* Hugging Face Transformers
* T5 (Text-to-Text Transfer Transformer)

### 🔹 Frontend

* HTML
* CSS
* JavaScript

---

## 📁 Project Structure

```
ai-ml-genai-project/
│
├── app.py
├── requirements.txt
│
├── data/
│   └── dataset.csv
│
├── models/
│   ├── model.pkl
│   └── vectorizer.pkl
│
├── src/
│   ├── train_ml.py
│   ├── intent_ml.py
│   └── generator.py
│
├── static/
│   ├── style.css
│   └── script.js
│
└── templates/
    └── index.html
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```
git clone https://github.com/your-username/ai-ml-genai-project.git
cd ai-ml-genai-project
```

### 2️⃣ Create Virtual Environment

```
python -m venv venv
```

### 3️⃣ Activate Environment

```
venv\Scripts\activate
```

### 4️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 5️⃣ Train ML Model

```
python src/train_ml.py
```

### 6️⃣ Run Application

```
python app.py
```

---

## 🧪 Example Inputs

* "Hello"
* "I want a refund"
* "App not working"
* "Tell me about your services"
* "This is the worst service ever"

---

## 📸 UI Features

* Chat bubbles (User & Bot)
* Typing animation
* Auto scroll
* Clean modern UI

---

## 🎯 Use Cases

* Customer Support Automation
* FAQ Bots
* Helpdesk Systems
* E-commerce Support

---

## 💡 Future Enhancements

* 🔊 Voice Input
* 🌙 Dark Mode
* 🧠 Context Memory
* 📊 Analytics Dashboard
* 🌐 Multi-language support

---

## 📌 Author

👤 Umang Singh

---

## ⭐ Contribution

Feel free to fork this repository and improve the chatbot!

---
