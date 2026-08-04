import pandas as pd
import pickle
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Load vectorizer
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Load dataset
df = pd.read_csv("datasets/cleaned_dataset.csv")

# Remove empty text rows
df = df.dropna(subset=['text'])

X = df['text']
y = df['label']

# Convert text to vectors
X_vec = vectorizer.transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

# Predict
pred = model.predict(X_test)

print("\n📊 Accuracy:", accuracy_score(y_test, pred))
print("\n📄 Classification Report:\n", classification_report(y_test, pred))
print("\n🧮 Confusion Matrix:\n", confusion_matrix(y_test, pred))