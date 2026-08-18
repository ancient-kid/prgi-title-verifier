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

# Stage 4 Similarity Thresholds (0.0 to 1.0)
ORTHOGRAPHIC_THRESHOLD = float(os.getenv("ORTHOGRAPHIC_THRESHOLD", "0.65"))
PHONETIC_THRESHOLD = float(os.getenv("PHONETIC_THRESHOLD", "0.70"))
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", "0.70"))
OVERALL_REJECTION_THRESHOLD = float(os.getenv("OVERALL_REJECTION_THRESHOLD", "0.65"))

# Stage 4A: Phonetic Configuration
PHONETIC_SHORT_WORD_MAX_LEN = int(os.getenv("PHONETIC_SHORT_WORD_MAX_LEN", "4"))
PHONETIC_SHORT_WORD_MIN_CHAR_SIM = float(os.getenv("PHONETIC_SHORT_WORD_MIN_CHAR_SIM", "0.80"))
PHONETIC_MATCH_THRESHOLD = float(os.getenv("PHONETIC_MATCH_THRESHOLD", "0.70"))

# Stage 4B: Orthographic Configuration
NGRAM_SIZE = int(os.getenv("NGRAM_SIZE", "3"))
ORTHOGRAPHIC_AGGREGATION_POLICY = os.getenv("ORTHOGRAPHIC_AGGREGATION_POLICY", "max")

# Stage 4C: Semantic Configuration
SEMANTIC_VECTOR_DIM = int(os.getenv("SEMANTIC_VECTOR_DIM", "2048"))
SEMANTIC_MATCH_THRESHOLD = float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.70"))

# Pipeline Search Configuration
MAX_CANDIDATE_SEARCH = int(os.getenv("MAX_CANDIDATE_SEARCH", "100"))
TOP_MATCHES_RETURN = int(os.getenv("TOP_MATCHES_RETURN", "5"))

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
