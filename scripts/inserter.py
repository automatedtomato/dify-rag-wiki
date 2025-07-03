# scripts/inserter.py
"""
Sets up the database and inserts articles from the JSONL file.
"""
import json
import os
import sys
from logging import getLogger

from tqdm import tqdm

sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Article
from scripts.common.log_setting import setup_logger

# --- Logger Setup ---
logger = getLogger(__name__)
logger = setup_logger(logger=logger)

# --- Constants ---
INPUT_JSONL_PATH = os.path.join("data/raw", "articles.jsonl")
BATCH_SIZE = 1000


def main():
    """
    Sets up the database and inserts articles from the JSONL file.
    """
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:mysecretpassword123@localhost:5432/chatbot_db",
    )
    engine = create_engine(DATABASE_URL)

    SessionLocal_script = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal_script() as db:
        logger.info("Deleting old article data...")
        num_deleted = db.query(Article).delete()
        db.commit()
        logger.info(f"{num_deleted} articles deleted.")

        logger.info(f"Starting to insert articles from {INPUT_JSONL_PATH}...")
        article_buffer = []
        saved_count = 0
        try:
            with open(INPUT_JSONL_PATH, "r", encoding="utf-8") as f:
                # Get total line count for tqdm progress bar
                total_lines = sum(1 for _ in f)
                f.seek(0)

                for line in tqdm(f, total=total_lines, desc="Inserting articles"):
                    data = json.loads(line)
                    new_article = Article(**data)
                    article_buffer.append(new_article)

                    if len(article_buffer) >= BATCH_SIZE:
                        db.bulk_save_objects(article_buffer)
                        db.commit()
                        saved_count += len(article_buffer)
                        article_buffer = []

            if article_buffer:
                db.bulk_save_objects(article_buffer)
                db.commit()
                saved_count += len(article_buffer)

            logger.info(
                f"Process complete. A total of {saved_count} articles have been inserted."
            )
        except FileNotFoundError:
            logger.error(
                f"Input file not found: {INPUT_JSONL_PATH}. Please run the parser script first."
            )
            sys.exit(1)
        except Exception as e:
            logger.error(f"An error occurred during DB insertion: {e}", exc_info=True)
            db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    main()
