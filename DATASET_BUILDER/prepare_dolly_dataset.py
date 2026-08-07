import os
import sys
import json
import csv
import urllib.request
import argparse
from typing import List, Dict

DOLLY_15K_URL = "https://raw.githubusercontent.com/databrickslabs/dolly/master/data/databricks-dolly-15k.jsonl"

def download_and_prepare_dolly(sample_per_category: int = 10, output_csv: str = "data/dolly_prompts.csv"):
    """
    Downloads databricks-dolly-15k dataset directly from GitHub,
    samples records across categories, and converts them to CSV format.
    """
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    
    local_file_path = os.path.join(os.path.dirname(__file__), "databricks-dolly-15k.jsonl")
    print(f"Reading databricks-dolly-15k dataset from {local_file_path}...")
    try:
        with open(local_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"Successfully read Dolly 15k dataset. Total records found: {len(lines)}")
    except Exception as e:
        print(f"Error reading Dolly dataset locally: {e}")
        sys.exit(1)

    # Group prompts by category
    categories_data: Dict[str, List[Dict[str, str]]] = {}

    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            instruction = item.get("instruction", "").strip()
            context = item.get("context", "").strip()
            category = item.get("category", "general").strip()

            # Formulate prompt
            if context:
                prompt = f"Context: {context}\n\nTask: {instruction}"
            else:
                prompt = instruction

            if not prompt:
                continue

            if category not in categories_data:
                categories_data[category] = []
            
            categories_data[category].append({
                "prompt": prompt,
                "category": category,
                "reference_response": item.get("response", "")
            })
        except Exception:
            continue

    print(f"\nDiscovered categories in databricks-dolly-15k:")
    for cat, records in categories_data.items():
        print(f"  - {cat}: {len(records)} total records")

    # Sample records per category
    sampled_records = []
    for cat, records in categories_data.items():
        sub_sample = records[:sample_per_category]
        sampled_records.extend(sub_sample)
        print(f"Sampled {len(sub_sample)} records for category '{cat}'")

    # Save to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prompt", "category", "reference_response"])
        writer.writeheader()
        writer.writerows(sampled_records)

    print(f"\nSUCCESS! Saved {len(sampled_records)} Dolly prompts to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and prepare Databricks Dolly 15k prompts for LLM Autopilot benchmark.")
    parser.add_argument("--sample", "-s", type=int, default=10, help="Number of prompts to sample per category (default: 10).")
    parser.add_argument("--output", "-o", type=str, default="data/dolly_prompts.csv", help="Output CSV path (default: data/dolly_prompts.csv).")
    args = parser.parse_args()

    download_and_prepare_dolly(sample_per_category=args.sample, output_csv=args.output)
