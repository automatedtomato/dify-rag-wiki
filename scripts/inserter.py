import json
import os
import sys
from logging import getLogger

from tqdm import tqdm

sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.models import Article, Base
from scripts.common.log_setting import setup_logger

# --- Logger Setup ---
logger = getLogger(__name__)
logger = setup_logger(logger=logger)

# --- Constants ---
INPUT_JSONL_PATH = os.path.join("data/raw", "articles.jsonl")
BATCH_SIZE = 1000


def setup_database(engine):
    """Sets up database prerequisites (extensions, tables)."""
    try:
        with engine.connect() as connection:
            with connection.begin():
                logger.info("Enabling required DB extensions: pg_trgm, vector...")
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("Extensions enabled successfully.")
    except Exception as e:
        logger.error(f"Failed to enable extensions: {e}", exc_info=True)
        raise

    try:
        logger.info("Ensuring all tables exist...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables are ready.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}", exc_info=True)
        raise


def main():
    """
    Sets up the database and inserts articles from the JSONL file.
    """
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:mysecretpassword123@localhost:5432/chatbot_db",
    )
    engine = create_engine(DATABASE_URL)

    # Step 1: Setup database prerequisites
    setup_database(engine)

    # Step 2: Insert data
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
                # To show a progress bar, we need the total number of lines first.
                total_lines = sum(1 for line in f)
                f.seek(0)  # Reset file pointer to the beginning

                for line in tqdm(f, total=total_lines, desc="Inserting articles"):
                    data = json.loads(line)
                    # Using **data to unpack the dictionary into keyword arguments
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
                f"Process complete. \
                    A total of {saved_count} articles have been inserted."
            )
        except FileNotFoundError:
            logger.error(
                f"Input file not found: {INPUT_JSONL_PATH}. \
                    Please run the parser script first."
            )
            sys.exit(1)
        except Exception as e:
            logger.error(f"An error occurred during DB insertion: {e}", exc_info=True)
            db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    main()
