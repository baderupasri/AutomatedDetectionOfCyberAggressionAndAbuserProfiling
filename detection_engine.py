import pickle
import re

# Load trained model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)


# Safe messages that should never be blocked
SAFE_WORDS = [
    "hi",
    "hello",
    "hey",
    "good morning",
    "good evening",
    "how are you",
    "nice to meet you"
]


# Strong aggressive keywords
AGGRESSIVE_WORDS = [
    "idiot",
    "stupid",
    "loser",
    "dumb",
    "hate you",
    "kill yourself",
    "shut up"
]


def clean_text(text):

    text = str(text).lower()

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)

    return text


def predict_aggression(message):

    text = clean_text(message)

    # -------- Rule 1 : Safe words --------
    for word in SAFE_WORDS:
        if word in text:
            return {
                "label": "SAFE",
                "blocked": False
            }

    # -------- Rule 2 : Strong aggressive keywords --------
    for word in AGGRESSIVE_WORDS:
        if word in text:
            return {
                "label": "AGGRESSIVE",
                "blocked": True
            }

    # -------- Rule 3 : Machine Learning Model --------
    vec = vectorizer.transform([text])

    probability = model.predict_proba(vec)[0][1]

    if probability > 0.80:
        return {
            "label": "AGGRESSIVE",
            "blocked": True
        }
    else:
        return {
            "label": "SAFE",
            "blocked": False
        }