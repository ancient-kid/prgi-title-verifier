import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Ensure data dir exists
os.makedirs(DATA_DIR, exist_ok=True)

# File paths
TITLES_FILE = BASE_DIR / "titles.xlsx"
TITLES_PARQUET_FILE = DATA_DIR / "titles.parquet"
TITLES_SQLITE_FILE = DATA_DIR / "titles.db"
EMBEDDINGS_CACHE_FILE = DATA_DIR / "title_embeddings.npy"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{TITLES_SQLITE_FILE}")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_LOCK_TTL_SECONDS = int(os.getenv("REDIS_LOCK_TTL_SECONDS", "600"))  # 10 minutes default

# Similarity Thresholds (0.0 to 1.0)
ORTHOGRAPHIC_THRESHOLD = float(os.getenv("ORTHOGRAPHIC_THRESHOLD", "0.65"))
PHONETIC_THRESHOLD = float(os.getenv("PHONETIC_THRESHOLD", "0.70"))
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", "0.70"))
OVERALL_REJECTION_THRESHOLD = float(os.getenv("OVERALL_REJECTION_THRESHOLD", "0.65"))

# Pipeline configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
MAX_CANDIDATE_SEARCH = int(os.getenv("MAX_CANDIDATE_SEARCH", "200"))
TOP_MATCHES_RETURN = int(os.getenv("TOP_MATCHES_RETURN", "5"))

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
