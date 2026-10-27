import json
import os
import sys
import pickle
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from preprocess import preprocess, tokenize, remove_stopwords, stem, lemmatize, clean_text, light_clean
from keywords import top_keywords, aspect_breakdown
from train_nextword import predict_next, SEQ

LABELS = ["negative", "neutral", "positive"]
ICON = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}

st.set_page_config(page_title="Course Feedback Analyzer", page_icon="🎓", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 8% 0%, rgba(59, 130, 246, 0.20), transparent 30%),
            radial-gradient(ellipse at 92% 14%, rgba(34, 211, 238, 0.12), transparent 28%),
            linear-gradient(180deg, #071a2d 0%, #0c2137 52%, #0d1b2d 100%);
        color: #EAF4FF;
    }
    [data-testid="stHeader"] {
        background: rgba(8, 20, 33, 0.9);
    }
    [data-testid="stMainBlockContainer"] {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1440px;
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem;
        margin-bottom: 1.4rem;
        border: 1px solid rgba(137, 180, 255, 0.18);
        border-radius: 24px;
        color: #ffffff;
        background: linear-gradient(115deg, #0b223f 0%, #123c68 45%, #1f74d5 100%);
        box-shadow: 0 18px 42px rgba(5, 18, 31, 0.42);
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 250px;
        height: 250px;
        right: -60px;
        top: -105px;
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 50%;
        box-shadow: 0 0 0 28px rgba(255, 255, 255, 0.04), 0 0 0 58px rgba(255, 255, 255, 0.03);
    }
    .hero-kicker {
        margin-bottom: 0.65rem;
        color: #D9ECFF;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: 0;
        color: #ffffff;
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.08;
    }
    .hero p {
        max-width: 700px;
        margin: 0.8rem 0 0;
        color: #EAF4FF;
        font-size: 1rem;
        line-height: 1.6;
    }
    .section-heading {
        margin: 1.6rem 0 0.25rem;
        color: #10233E;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    .section-caption {
        margin-bottom: 0.9rem;
        color: #4F6D8A;
        font-size: 0.92rem;
    }
    [data-testid="stMetric"] {
        min-height: 116px;
        padding: 1.05rem 1.15rem;
        border: 1px solid rgba(154, 181, 231, 0.22);
        border-radius: 17px;
        background: rgba(13, 30, 45, 0.68);
        box-shadow: 0 8px 22px rgba(2, 8, 18, 0.18);
    }
    [data-testid="stMetricLabel"] {
        color: #A9C5E7;
        font-size: 0.84rem;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #F0F7FF;
        font-weight: 750;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(11, 23, 38, 0.96) 0%, rgba(17, 31, 49, 0.96) 100%);
        border-right: 1px solid rgba(159, 184, 235, 0.18);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 0.62rem 0.72rem;
        border-radius: 11px;
        color: #E6F1FF;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(92, 153, 255, 0.12);
    }
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {
        border: 1px solid rgba(112, 160, 255, 0.35);
        border-radius: 13px;
        background: rgba(11, 24, 38, 0.75);
        color: #EAF4FF;
    }
    [data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stTextInput"] input::placeholder {
        color: #8FAFCF;
    }
    [data-testid="stFileUploader"] section {
        border: 1px dashed rgba(117, 167, 255, 0.58);
        border-radius: 14px;
        background: rgba(12, 30, 47, 0.8);
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(154, 181, 231, 0.22);
        border-radius: 12px;
    }
    [data-testid="stAlert"] {
        background: rgba(13, 31, 48, 0.9);
        color: #EAF4FF;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        color: #DDEEFF;
    }
    [data-testid="stBaseButton-primary"] {
        border: 0;
        border-radius: 10px;
        background: linear-gradient(110deg, #1d74d7, #3b82f6);
        box-shadow: 0 5px 14px rgba(45, 119, 255, 0.25);
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(110deg, #1f66be, #2c6de6);
        border-color: transparent;
    }
    [data-testid="stBaseButton-secondary"] {
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.92);
        color: #0b223f;
        font-weight: 600;
        box-shadow: 0 6px 16px rgba(2, 10, 20, 0.12);
    }
    [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(255, 255, 255, 1);
        border-color: rgba(255, 255, 255, 0.35);
    }
    div[data-testid="stButton"] > button {
        background: rgba(255, 255, 255, 0.96);
        color: #0b223f !important;
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        padding: 0.45rem 0.9rem;
        font-size: 0.88rem;
        font-weight: 700;
        box-shadow: 0 6px 16px rgba(2, 10, 20, 0.12);
        text-transform: none;
    }
    div[data-testid="stButton"] > button:hover {
        background: rgba(255, 255, 255, 1);
        border-color: rgba(255, 255, 255, 0.32);
        color: #0b223f !important;
    }
    div[data-testid="stButton"] > button > span,
    div[data-testid="stButton"] > button p,
    div[data-testid="stButton"] > button div {
        color: #0b223f !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(154, 181, 231, 0.22);
        border-radius: 17px;
        background: rgba(10, 22, 35, 0.78);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_models():
    from tensorflow.keras.models import load_model
    need = ["tfidf_lr.pkl", "nextword_gru.keras", "nextword_tokenizer.pkl"]
    if not all((ROOT / "models" / f).exists() for f in need):
        return None
    with open(ROOT / "models" / "tfidf_lr.pkl", "rb") as model_file:
        vectorizer, classifier = pickle.load(model_file)
    return dict(
        vectorizer=vectorizer,
        classifier=classifier,
        gru=load_model(ROOT / "models" / "nextword_gru.keras"),
        ntok=pickle.load(open(ROOT / "models" / "nextword_tokenizer.pkl", "rb")),
    )


M = load_models()
if M is None:
    st.error("Models not found. Run:  python src/generate_dataset.py && python src/train_sentiment.py && python src/train_nextword.py")
    st.stop()


def predict_proba(texts):
    cleaned = [preprocess(text) for text in texts]
    probabilities = M["classifier"].predict_proba(M["vectorizer"].transform(cleaned))
    class_order = [list(M["classifier"].classes_).index(i) for i in range(len(LABELS))]
    return probabilities[:, class_order]


def predict_labels(texts):
    return [LABELS[i] for i in predict_proba(texts).argmax(1)]


def suggest_next_words(text, k=3):
    raw = predict_next(M["gru"], M["ntok"], text, k=k)
    items = []
    seen = set()
    for word in raw:
        word = str(word).strip().lower()
        if not word or word in seen or len(word) <= 1:
            continue
        seen.add(word)
        items.append(word)
        if len(items) >= k:
            break

    if items:
        return items

    cleaned = light_clean(text).lower()
    fallback = {
        "teach": ["clearly", "effectively", "well"],
        "professor": ["was", "very", "helpful"],
        "teacher": ["was", "very", "supportive"],
        "course": ["was", "is", "very"],
        "exam": ["was", "felt", "too"],
        "assignment": ["was", "felt", "clear"],
        "lecture": ["was", "were", "clear"],
    }
    for key, suggestions in fallback.items():
        if key in cleaned:
            return suggestions[:k]
    return ["helpful", "clear", "engaging"][:k]


with st.sidebar:
    st.markdown("## 🎓 Feedback Lab")
    st.caption("Student voice, made actionable")
    st.markdown("---")
    selected_view = st.radio(
        "Explore the workspace",
        [
            "✍️  Analyze a review",
            "📊  Analyze many reviews",
            "🔬  NLP pipeline",
            "🏆  Model results",
        ],
        label_visibility="visible",
    )
    st.markdown("---")
    st.caption("SDG 4 · Quality education")

st.markdown(
    """
    <section class="hero">
      <div class="hero-kicker">Student voice · actionable insight</div>
      <h1>Course feedback, clearly understood.</h1>
      <p>Turn student reviews into sentiment, themes, and practical next steps.
      Explore a single comment or uncover patterns across an entire class.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

if selected_view == "✍️  Analyze a review":
    if "review" not in st.session_state:
        st.session_state.review = ""
    with st.container(border=True):
        st.markdown("### ✍️ Analyze a course review")
        st.caption("Sentiment uses TF-IDF + Logistic Regression, selected by held-out validation. Share a comment to see its sentiment and key themes.")
        review = st.text_area(
            "Write or paste a course review",
            key="review",
            height=130,
            placeholder="e.g. The professor was very helpful but the exams were too rushed.",
        )
        if review.strip():
            sugg = suggest_next_words(review, k=3)
            st.caption("💡 Suggested next words")
            cols = st.columns(len(sugg))
            for col, w in zip(cols, sugg):
                if col.button(f"{w}", key=f"s_{w}"):
                    st.session_state.review = review.rstrip() + " " + w
                    st.rerun()
            if st.button("Analyze review", type="primary", icon=":material/analytics:"):
                p = predict_proba([review])[0]
                lab = LABELS[int(p.argmax())]
                st.metric(
                    "Predicted sentiment",
                    f"{ICON[lab]} {lab.title()}",
                    f"{p.max()*100:.1f}% confidence",
                    border=True,
                )
                probability_chart = pd.DataFrame(
                    {"Sentiment": [label.title() for label in LABELS], "Probability": p}
                )
                sentiment_viz = (
                    alt.Chart(probability_chart)
                    .mark_bar(cornerRadiusEnd=8, size=28)
                    .encode(
                        x=alt.X("Sentiment:N", title=None, sort=None),
                        y=alt.Y("Probability:Q", title="Probability", axis=alt.Axis(format="%")),
                        color=alt.Color(
                            "Sentiment:N",
                            scale=alt.Scale(
                                domain=["Negative", "Neutral", "Positive"],
                                range=["#F87171", "#7DD3FC", "#34D399"],
                            ),
                            legend=None,
                        ),
                        tooltip=["Sentiment:N", "Probability:Q"],
                    )
                    .properties(height=170)
                    .configure_view(stroke=None)
                    .configure_axis(
                        labelColor="#DDEEFF",
                        titleColor="#C7D8EF",
                        gridColor="rgba(157, 196, 255, 0.2)",
                        domainColor="rgba(157, 196, 255, 0.2)",
                    )
                )
                st.altair_chart(sentiment_viz, use_container_width=True)
                kw = top_keywords([review], n=6, ngram=(1, 1))
                st.write("**Keywords (TF-IDF):** " + (", ".join(f"`{k}`" for k, _ in kw) or "-"))
                asp = aspect_breakdown([review], predict_labels)
                if len(asp):
                    st.write("**Aspects mentioned:**")
                    st.dataframe(asp[["Aspect", "positive", "neutral", "negative"]], hide_index=True)

sample_data = pd.read_csv(ROOT / "data" / "reviews.csv")
sentiment_counts = sample_data["sentiment"].value_counts().reindex(LABELS, fill_value=0)
metrics_path = ROOT / "reports" / "metrics.json"
model_metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
ranked_models = sorted(model_metrics.items(), key=lambda item: item[1].get("accuracy", 0), reverse=True)
best_accuracy = ranked_models[0][1].get("accuracy", 0) if ranked_models else 0
best_model_name = ranked_models[0][0] if ranked_models else "Not available"

st.markdown('<div class="section-heading">At a glance</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">A quick view of the sample feedback and trained model performance.</div>',
    unsafe_allow_html=True,
)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Reviews in sample", f"{len(sample_data):,}", border=True)
kpi2.metric("Positive feedback", f"{sentiment_counts['positive']:,}", border=True)
kpi3.metric("Negative feedback", f"{sentiment_counts['negative']:,}", border=True)
kpi4.metric("Best model accuracy", f"{best_accuracy:.1%}" if ranked_models else "—", border=True)

chart_left, chart_right = st.columns(2)
with chart_left:
    with st.container(border=True):
        st.markdown("**Sentiment mix**")
        st.caption("Labeled reviews in the sample dataset")
        sentiment_chart = pd.DataFrame(
            {
                "Sentiment": [label.title() for label in LABELS],
                "Reviews": [int(sentiment_counts[label]) for label in LABELS],
            }
        )
        sentiment_viz = (
            alt.Chart(sentiment_chart)
            .mark_bar(cornerRadiusEnd=7, size=30)
            .encode(
                x=alt.X("Reviews:Q", title="Number of reviews", scale=alt.Scale(domain=[0, len(sample_data)])),
                y=alt.Y("Sentiment:N", title=None, sort=["Positive", "Neutral", "Negative"]),
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Negative", "Neutral", "Positive"],
                        range=["#F87171", "#7DD3FC", "#2563EB"],
                    ),
                    legend=None,
                ),
                tooltip=["Sentiment:N", "Reviews:Q"],
            )
            .properties(height=170)
            .configure_view(stroke=None)
            .configure_axis(
                labelColor="#5E554C",
                titleColor="#766D63",
                gridColor="#E1D6C7",
                domainColor="#B9AA98",
            )
        )
        st.altair_chart(sentiment_viz, width="stretch")
with chart_right:
    with st.container(border=True):
        st.markdown("**Model leaderboard**")
        st.caption("Validation accuracy across trained models")
        if ranked_models:
            leaderboard = pd.DataFrame(
                {
                    "Model": [name for name, _ in ranked_models],
                    "Accuracy": [details.get("accuracy", 0) * 100 for _, details in ranked_models],
                }
            )
            leaderboard_viz = (
                alt.Chart(leaderboard)
                .mark_bar(cornerRadiusEnd=7, color="#3B82F6", size=22)
                .encode(
                    x=alt.X("Accuracy:Q", title="Validation accuracy (%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Model:N", title=None, sort="-x"),
                    tooltip=[
                        alt.Tooltip("Model:N", title="Model"),
                        alt.Tooltip("Accuracy:Q", title="Accuracy", format=".1f"),
                    ],
                )
                .properties(height=190)
                .configure_view(stroke=None)
                .configure_axis(
                    labelColor="#5E554C",
                    titleColor="#766D63",
                    gridColor="#E1D6C7",
                    domainColor="#B9AA98",
                )
            )
            st.altair_chart(leaderboard_viz, width="stretch")
        else:
            st.info("Train the models to see the comparison.")

if selected_view == "📊  Analyze many reviews":
    st.write("Upload a CSV with a **text** column, or paste one review per line.")
    up = st.file_uploader("CSV file", type="csv")
    pasted = st.text_area("...or paste reviews (one per line)", height=120)
    use_sample = st.checkbox("Use the built-in sample dataset (200 reviews)")
    texts = []
    if up is not None:
        d = pd.read_csv(up)
        col = "text" if "text" in d.columns else d.columns[0]
        texts = d[col].dropna().astype(str).tolist()
    elif pasted.strip():
        texts = [l for l in pasted.splitlines() if l.strip()]
    elif use_sample:
        texts = pd.read_csv(ROOT / "data" / "reviews.csv").text.head(200).tolist()
    if texts and st.button("Run analysis", type="primary"):
        labs = predict_labels(texts)
        res = pd.DataFrame({"review": texts, "sentiment": labs})
        a, b, c = st.columns(3)
        for col_, l in zip((a, b, c), ("positive", "neutral", "negative")):
            col_.metric(f"{ICON[l]} {l.title()}", f"{(res.sentiment == l).sum()}", f"{(res.sentiment == l).mean()*100:.0f}%")
        st.bar_chart(res.sentiment.value_counts().reindex(["positive", "neutral", "negative"]).fillna(0))
        left, right = st.columns(2)
        with left:
            st.subheader("Top keywords in complaints")
            neg = res[res.sentiment == "negative"].review.tolist()
            st.dataframe(pd.DataFrame(top_keywords(neg, 10), columns=["keyword", "tf-idf"]), hide_index=True)
        with right:
            st.subheader("Top keywords in praise")
            pos = res[res.sentiment == "positive"].review.tolist()
            st.dataframe(pd.DataFrame(top_keywords(pos, 10), columns=["keyword", "tf-idf"]), hide_index=True)
        st.subheader("Aspect-wise report (what to improve first)")
        st.caption("score = (positive - negative) / total mentions.  Lowest score = biggest problem area.")
        st.dataframe(aspect_breakdown(texts, predict_labels), hide_index=True)
        st.download_button("Download results CSV", res.to_csv(index=False), "analyzed_reviews.csv")

elif selected_view == "🔬  NLP pipeline":
    st.write("See every preprocessing step (Unit 1 experiments) on your own text.")
    demo = st.text_input("Text", "The lectures weren't great, but the teachers are really helpful!")
    toks = tokenize(demo)
    ns = remove_stopwords(toks)
    c1, c2 = st.columns(2)
    c1.write("**1. Cleaned (regex):**"); c1.code(clean_text(demo))
    c1.write("**2. Tokens:**"); c1.code(toks)
    c1.write("**3. Stop words removed:**"); c1.code(ns)
    c2.write("**4. Stemming (Porter):**"); c2.code(stem(ns))
    c2.write("**5. Lemmatization:**"); c2.code(lemmatize(ns))
    c2.write("**6. Final model input:**"); c2.code(preprocess(demo))
    st.info("Note: negations like *not* / *no* are intentionally kept - removing them would flip sentiment.")

elif selected_view == "🏆  Model results":
    mc = ROOT / "reports" / "model_comparison.csv"
    if mc.exists():
        st.dataframe(pd.read_csv(mc, index_col=0))
    for img, cap in (("model_comparison.png", "Model comparison"), ("training_curves.png", "Validation accuracy per epoch"), ("confusion_matrix.png", "LSTM confusion matrix"), ("word_frequency.png", "Word frequency: before vs after stop-word removal"), ("class_distribution.png", "Class distribution")):
        if (ROOT / "reports" / img).exists():
            st.image(str(ROOT / "reports" / img), caption=cap)
