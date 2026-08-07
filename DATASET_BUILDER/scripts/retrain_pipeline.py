import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def connect_db():
    db_url = os.environ.get(
        "DATABASE_URL", 
        "postgresql://postgres:secretpassword@localhost:5432/llm_autopilot"
    )
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def main():
    print("Starting Weekly Feedback Retraining Pipeline...")
    
    conn = connect_db()
    if not conn:
        print("Cannot proceed without database connection.")
        sys.exit(1)
        
    try:
        # Extract mismatches
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, prompt, premium_model, similarity_score 
                FROM shadow_evaluations 
                WHERE similarity_score < 0.85 
                AND processed_for_training = FALSE;
            """)
            failures = cur.fetchall()
            
        if not failures:
            print("No new shadow evaluation mismatches found. Classifier is up-to-date!")
            sys.exit(0)
            
        print(f"Discovered {len(failures)} new edge cases where the cheap model failed.")
        
        # Transform data to match training schema
        new_data = []
        record_ids = []
        for row in failures:
            new_data.append({
                "prompt": row["prompt"],
                "label": row["premium_model"]  # Assign premium model as the correct label
            })
            record_ids.append(row["id"])
            
        new_df = pd.DataFrame(new_data)
        
        # Load and append to master dataset
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/labeled_prompts.csv'))
        
        if os.path.exists(csv_path):
            print(f"Appending new failures to {csv_path}...")
            # We append without headers if the file exists, but to be safe we'll read and concat
            master_df = pd.read_csv(csv_path)
            master_df = pd.concat([master_df, new_df], ignore_index=True)
            master_df.to_csv(csv_path, index=False)
        else:
            print(f"Master dataset not found. Creating new dataset at {csv_path}...")
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            new_df.to_csv(csv_path, index=False)
            
        print(f"Successfully integrated {len(failures)} new rows into training dataset.")
        
        # Update Database flag
        with conn.cursor() as cur:
            # PostgreSQL requires a tuple for IN clause
            cur.execute(
                "UPDATE shadow_evaluations SET processed_for_training = TRUE WHERE id IN %s;",
                (tuple(record_ids),)
            )
        print("Marked records as processed in the database.")
        
        # Trigger retraining
        print("\n--- Triggering ML Classifier Retraining ---")
        train_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../train_classifier.py'))
        
        result = subprocess.run(
            [sys.executable, train_script_path, "--dataset", csv_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Retraining completed successfully!")
            print(result.stdout)
        else:
            print("ERROR: Retraining failed.")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Pipeline failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
