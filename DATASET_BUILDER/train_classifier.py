import os
import sys
import argparse
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from router.semantic_cache import SemanticCache

def main():
    parser = argparse.ArgumentParser(description="Train ML Classifier for LLM Cost Autopilot router using benchmark dataset.")
    parser.add_argument(
        "--dataset", "-d", 
        type=str, 
        default="data/model_benchmark_dataset.csv",
        help="Path to labeled benchmark dataset CSV (default: data/model_benchmark_dataset.csv)"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        default="router/classifier_model.joblib", 
        help="Output path for trained joblib model (default: router/classifier_model.joblib)"
    )
    args = parser.parse_args()

    csv_path = args.dataset
    if not os.path.exists(csv_path):
        # Fallback check for labeled_prompts.csv
        fallback = "data/labeled_prompts.csv"
        if os.path.exists(fallback):
            print(f"Dataset '{csv_path}' not found. Falling back to '{fallback}'.")
            csv_path = fallback
        else:
            print(f"ERROR: Dataset not found at '{csv_path}'. Please run benchmark_dataset_builder.py first.")
            sys.exit(1)

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    if "prompt" not in df.columns or "label" not in df.columns:
        print("ERROR: CSV must contain 'prompt' and 'label' columns.")
        sys.exit(1)

    print(f"Dataset loaded successfully. Total records: {len(df)}")
    print("Label distribution (Best LLM / Tier):")
    print(df["label"].value_counts())

    # Initialize SemanticCache helper to get local embedding generator
    print("\nInitializing embedding generator (sentence-transformers / MiniLM)...")
    cache_helper = SemanticCache()

    print("Generating embeddings for all prompts in dataset...")
    embeddings = []
    for idx, prompt in enumerate(df["prompt"]):
        if idx > 0 and idx % 20 == 0:
            print(f"  Processed {idx}/{len(df)} prompts...")
        emb = cache_helper.get_embedding(str(prompt))
        embeddings.append(emb)

    X = np.array(embeddings)
    y = df["label"].values

    print(f"\nFeatures matrix shape: {X.shape}")
    print(f"Labels shape: {y.shape}")

    # Train Logistic Regression classifier
    print("Training Logistic Regression router model...")
    clf = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    clf.fit(X, y)

    # Prepare model metadata payload
    model_data = {
        "classifier": clf,
        "classes": clf.classes_.tolist(),
        "embedding_type": "local" if cache_helper.local_embedding_model else "api",
        "dimension": cache_helper.dimension
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    joblib.dump(model_data, args.output)

    train_acc = clf.score(X, y)
    print(f"\nTraining accuracy: {train_acc * 100:.2f}%")
    print(f"SUCCESS! Saved trained ML classifier model to {args.output}!")

if __name__ == "__main__":
    main()
