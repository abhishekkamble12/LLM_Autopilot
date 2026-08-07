import os
import sys
import numpy as np
from typing import List, Dict, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_LIBRARIES_AVAILABLE = True
except ImportError:
    DB_LIBRARIES_AVAILABLE = False

# Import provider package for fallback embedding generator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from providers import GeminiProvider

class SemanticCache:
    """
    Semantic Cache class that uses PostgreSQL with pgvector extension
    to cache prompt responses based on embedding similarity.
    """

    def __init__(
        self,
        db_url: str = None,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        dimension: int = 384
    ):
        self.db_url = db_url or os.environ.get(
            "DATABASE_URL", 
            "postgresql://postgres:secretpassword@localhost:5432/llm_autopilot"
        )
        self.dimension = dimension
        self.db_connected = False
        self.conn = None
        
        # Initialize embedding model locally if possible, or fall back to GeminiProvider/OpenRouter
        self.local_embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading local embedding model: {embedding_model_name}...")
            self.local_embedding_model = SentenceTransformer(embedding_model_name)
            self.dimension = 384 # MiniLM dimension
            print("Local embedding model loaded successfully.")
        except ImportError:
            print("sentence-transformers not installed. Will use OpenRouter embedding API as fallback.")
            self.dimension = 1536 # OpenRouter text-embedding-3-small dimension
            self.fallback_provider = GeminiProvider()

        # Connect to DB
        if DB_LIBRARIES_AVAILABLE:
            self._connect_db()

    def _connect_db(self):
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
            
            # Setup extension and table if they don't exist
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS prompt_logs (
                        id SERIAL PRIMARY KEY,
                        prompt TEXT NOT NULL,
                        embedding vector({self.dimension}),
                        response TEXT NOT NULL,
                        model_used VARCHAR(100) NOT NULL,
                        cost NUMERIC(10, 6) NOT NULL,
                        savings NUMERIC(10, 6) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS shadow_evaluations (
                        id SERIAL PRIMARY KEY,
                        prompt TEXT NOT NULL,
                        cheap_model VARCHAR(100),
                        cheap_response TEXT,
                        premium_model VARCHAR(100),
                        premium_response TEXT,
                        similarity_score FLOAT,
                        processed_for_training BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("ALTER TABLE prompt_logs ADD COLUMN IF NOT EXISTS feedback VARCHAR(10) DEFAULT 'unrated';")
                # Create an index for vector similarity search
                cur.execute("CREATE INDEX IF NOT EXISTS prompt_logs_embedding_idx ON prompt_logs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
            self.db_connected = True
            print("Successfully connected to Postgres and initialized vector tables.")
        except Exception as e:
            print(f"Database connection failed: {e}. Running in cache-bypass mode.")
            self.db_connected = False

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the input text. Uses sentence-transformers locally
        or falls back to OpenRouter API.
        """
        if self.local_embedding_model:
            emb = self.local_embedding_model.encode(text)
            return emb.tolist()
        else:
            # Call OpenRouter embedding model
            import asyncio
            return asyncio.run(self.fallback_provider.embedding(text))

    async def lookup(self, prompt: str, threshold: float = 0.08) -> Optional[Dict[str, Any]]:
        """
        Looks up the prompt in pgvector. Returns the cached response if similarity distance < threshold.
        (threshold 0.08 on cosine distance ~= 92% similarity).
        """
        if not DB_LIBRARIES_AVAILABLE or not self.db_connected:
            return None

        try:
            embedding = self.get_embedding(prompt)
            
            # Perform vector search using cosine distance (<=> operator in pgvector)
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, response, model_used, cost, savings, (embedding <=> %s::vector) AS distance
                    FROM prompt_logs
                    ORDER BY distance ASC
                    LIMIT 1;
                    """,
                    (embedding,)
                )
                row = cur.fetchone()
                
                if row and row['distance'] < threshold:
                    print(f"Semantic cache HIT! Distance: {row['distance']:.4f}")
                    return {
                        "id": int(row["id"]),
                        "response": row["response"],
                        "model_used": row["model_used"],
                        "cost": 0.0, # Cached responses cost nothing
                        "savings": float(row["savings"]), # The savings equal what it would have costed originally
                        "distance": float(row["distance"])
                    }
        except Exception as e:
            print(f"Semantic Cache Lookup Error: {e}")
            # Try to reconnect database if connection lost
            self._connect_db()
        
        return None

    def insert(
        self,
        prompt: str,
        response: str,
        model_used: str,
        cost: float,
        savings: float
    ) -> Optional[int]:
        """
        Inserts a new query log with its embedding vector into the database. Returns the log id.
        """
        if not DB_LIBRARIES_AVAILABLE or not self.db_connected:
            return None

        try:
            embedding = self.get_embedding(prompt)
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO prompt_logs (prompt, embedding, response, model_used, cost, savings)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (prompt, embedding, response, model_used, cost, savings)
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Failed to log record in database: {e}")
            return None

    def update_feedback(self, log_id: int, feedback: str) -> bool:
        """
        Updates the feedback field for a specific log id.
        """
        if not DB_LIBRARIES_AVAILABLE or not self.db_connected:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE prompt_logs SET feedback = %s WHERE id = %s;",
                    (feedback, log_id)
                )
                return True
        except Exception as e:
            print(f"Failed to update feedback for log {log_id}: {e}")
            return False
    






    
