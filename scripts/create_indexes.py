import logging
import os
import sys
from logging import Formatter, StreamHandler, getLogger

from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from backend.app.database import SessionLocal

# ========== Logging Config ==========
logger = getLogger(__name__)

FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


def create_gin_indexes():
    """
    Create GIN indexes on articles table
    """

    logger.info("Creating GIN indexes...(this may take a while)")

    try:
        with SessionLocal() as db:
            # Check pg_trgm extension
            logger.info("Checking pg_trgm extension...")
            db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            db.commit()
            logger.info("pg_trgm extension enabled")

            # title index
            logger.info("Create title index...")
            db.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_articles_title_gin
                    ON articles USING gin (title gin_trgm_ops);
                    """
                )
            )
            db.commit()
            logger.info("Title indexes created")

            # content index
            logger.info("Create content index...")
            db.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_articles_content_gin
                    ON articles USING gin (content gin_trgm_ops);
                    """
                )
            )
            db.commit()
            logger.info("Content indexes created")

        logger.info("All indexes created")

    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


if __name__ == "__main__":
    create_gin_indexes()
