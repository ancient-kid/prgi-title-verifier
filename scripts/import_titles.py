"""
Data Import & Database Synchronization Script for PRGI Master Registered Titles Dataset
"""

import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import pandas as pd
from backend.config import DATA_DIR, TITLES_FILE, TITLES_PARQUET_FILE, TITLES_SQLITE_FILE
from backend.data_loader import TitleIndex
from backend.database import RegisteredTitleModel, SessionLocal, init_db


def run_import(max_rows=None):
    print("=" * 60)
    print("PRGI Title Verification System - Data Import Utility")
    print("=" * 60)
    
    start_time = time.perf_counter()
    init_db()
    
    indexer = TitleIndex()
    count = indexer.load_data(TITLES_FILE, max_rows=max_rows)
    
    print(f"[Import] Loaded & Indexed {count} titles.")
    
    # Sync to SQLite / PostgreSQL database
    db = SessionLocal()
    try:
        existing_count = db.query(RegisteredTitleModel).count()
        print(f"[DB] Current titles in relational DB: {existing_count}")
        
        if existing_count < count:
            print("[DB] Synchronizing records into relational database table...")
            batch_size = 5000
            records_to_insert = []
            
            for item in indexer.titles_data:
                record = RegisteredTitleModel(
                    title=item["title"],
                    cleaned_title=item["cleaned_title"],
                    anchor_words=item["anchor_words"],
                    registration_no=item["registration_no"],
                    language=item["language"],
                    state=item["state"],
                    periodicity=item["periodicity"],
                    phonetic_metaphone=item["phonetic_fingerprint"]["metaphone_str"],
                    indic_soundex=item["phonetic_fingerprint"]["indic_soundex_str"]
                )
                records_to_insert.append(record)
                
                if len(records_to_insert) >= batch_size:
                    db.bulk_save_objects(records_to_insert)
                    db.commit()
                    records_to_insert = []
                    print(f"[DB] Synced batch to database...")
                    
            if records_to_insert:
                db.bulk_save_objects(records_to_insert)
                db.commit()
                
            print(f"[DB] Successfully synced {count} records to database.")
    except Exception as e:
        print(f"[DB] Relational sync note: {e}")
        db.rollback()
    finally:
        db.close()
        
    elapsed = round(time.perf_counter() - start_time, 2)
    print(f"[Complete] Ingestion and indexing completed in {elapsed} seconds.")


if __name__ == "__main__":
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_import(max_rows=rows)
