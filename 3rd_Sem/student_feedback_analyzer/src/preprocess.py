"""NLP preprocessing: regex cleaning, tokenization, stop-word removal,
stemming and lemmatization (Unit 1 + Unit 2 of the syllabus)."""
import re
from nltk.stem import PorterStemmer

# Negations are deliberately KEPT: "not good" must stay different from "good".
_NEGATIONS = {"not", "no", "never", "nor", "n't", "cannot", "without", "hardly"}
STOP_WORDS = set("""
a about above after again all am an and any are as at be because been before being below
between both but by can did do does doing down during each few for from further had has have
having he her here hers herself him himself his how i if in into is it its itself just me more
most my myself of off on once only or other our ours ourselves out over own same she should so
some such than that the their theirs them themselves then there these they this those through to
too under until up very was we were what when where which while who whom why will with you your
yours yourself yourselves also get got would could course class
""".split()) - _NEGATIONS

_stemmer = PorterStemmer()

try:  # real WordNet lemmatizer if the corpus is installed
    from nltk.stem import WordNetLemmatizer
    _wn = WordNetLemmatizer()
    _wn.lemmatize("tests")
except Exception:
    _wn = None


def _rule_lemma(w: str) -> str:
    """Tiny rule-based lemmatizer used when WordNet is unavailable."""
    irregular = {"was": "be", "were": "be", "is": "be", "are": "be", "better": "good",
                 "best": "good", "worse": "bad", "worst": "bad", "taught": "teach",
                 "went": "go", "gave": "give", "made": "make"}
    if w in irregular:
        return irregular[w]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def clean_text(text: str) -> str:
    """Lower-case and strip URLs, emails, HTML, digits and punctuation with regex."""
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"<.*?>", " ", text)
    text = text.replace("n't", " not")
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str):
    return clean_text(text).split()


def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def stem(tokens):
    return [_stemmer.stem(t) for t in tokens]


def lemmatize(tokens):
    if _wn is not None:
        return [_wn.lemmatize(t) for t in tokens]
    return [_rule_lemma(t) for t in tokens]


def preprocess(text: str, use_lemma: bool = True) -> str:
    """Full pipeline -> a clean space-joined string (used for TF-IDF / LSTM)."""
    toks = remove_stopwords(tokenize(text))
    toks = lemmatize(toks) if use_lemma else toks
    return " ".join(toks)


def light_clean(text: str) -> str:
    """Keeps stop-words (needed for next-word prediction, where grammar matters)."""
    return clean_text(text)


if __name__ == "__main__":
    s = "The lectures weren't great, but the teachers are helpful! Visit http://x.com"
    print("clean   :", clean_text(s))
    print("tokens  :", tokenize(s))
    print("no stop :", remove_stopwords(tokenize(s)))
    print("stem    :", stem(remove_stopwords(tokenize(s))))
    print("lemma   :", lemmatize(remove_stopwords(tokenize(s))))
