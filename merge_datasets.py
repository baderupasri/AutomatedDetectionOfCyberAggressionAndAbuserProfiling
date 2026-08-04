import pandas as pd

# Load datasets
harras = pd.read_csv("datasets/cyberbullying-and-harrasment/dataset1.csv")
cyber = pd.read_csv("datasets/cyberbullying-classification/dataset2.csv")
tweet = pd.read_csv("datasets/cyberbullying-tweets/dataset3.csv")
#offensive = pd.read_csv("datasets/hate-speech-and-offensive-language-dataset/dataset4.csv")

# -------- Dataset 1 (Harassment dataset) --------
harras_df = harras[['Text','Label']]
harras_df.columns = ['text','label']

# Convert labels to numbers
harras_df['label'] = harras_df['label'].apply(
    lambda x: 1 if "Bullying" in str(x) else 0
)

# -------- Dataset 2 (Cyberbullying dataset) --------
cyber_df = cyber[['tweet_text', 'cyberbullying_type']]
cyber_df.columns = ['text', 'label']

cyber_df['label'] = cyber_df['label'].apply(lambda x: 1 if x != 'not_cyberbullying' else 0)


# -------- Dataset 3 (Tweets dataset) --------
tweet_df = tweet[['Text', 'CB_Label']]
tweet_df.columns = ['text', 'label']

tweet_df['label'] = tweet_df['label'].apply(lambda x: 1 if x in [0,1] else 0)


# -------- Dataset 4 (Offensive language dataset) --------
#offensive_df = offensive[['tweet', 'class']]
#offensive_df.columns = ['text', 'label']

#offensive_df['label'] = offensive_df['label'].apply(lambda x: 1 if x in [0,1] else 0)


# -------- Merge all datasets --------
merged = pd.concat([harras_df, cyber_df, tweet_df], axis=0)

# Shuffle dataset
merged = merged.sample(frac=1).reset_index(drop=True)

# Save merged dataset
merged.to_csv("datasets/merged_dataset.csv", index=False)

print("✅ merged_dataset.csv created successfully")