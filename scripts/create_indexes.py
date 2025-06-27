import logging
import os
import sys
from logging import Formatter, StreamHandler, getLogger

from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.getcwd())

from backend.app.database import SessionLocal

# ========== SQL Commands ==========
SQL_COMMANDS = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
    "CREATE EXTENSION IF NOT EXISTS vector;",
    "CREATE INDEX IF NOT EXISTS idx_articles_title_gin ON articles USING gin (title gin_trgm_ops);",
    "CREATE INDEX IF NOT EXISTS idx_articles_content_gin ON articles USING gin (content gin_trgm_ops);",
    "CREATE INDEX IF NOT EXISTS idx_articles_vector ON articles USING hnsw (content_vector vector_l2_ops);",
]

# ========== Logging Config ==========
logger = getLogger(__name__)

FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


def main():
    logger.info("Creating GIN indexes (this may take a while)...")
    try:
        with SessionLocal() as db:
            db.execute(text("SET statement_timeout = 0;"))
            for sql_command in SQL_COMMANDS:
                db.execute(text(sql_command))
                db.commit()

        logger.info("GIN indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create GIN indexes: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
