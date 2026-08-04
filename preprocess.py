import pandas as pd
import re
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

df = pd.read_csv("datasets/merged_dataset.csv")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

df['text'] = df['text'].apply(clean_text)

df.to_csv("datasets/cleaned_dataset.csv", index=False)

print("✅ cleaned_dataset.csv created successfully")
