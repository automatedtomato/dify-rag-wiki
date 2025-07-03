# This script is responsible ONLY for setting up the database schema.

import sys
import os
from logging import getLogger, Formatter, StreamHandler

sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from backend.app.models import Base
from scripts.common.log_setting import setup_logger

# --- Logger Setup ---
logger = getLogger(__name__)
logger = setup_logger(logger=logger)

def main():
    """
    Enables required extensions and creates all tables from the models.
    """
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:mysecretpassword123@localhost:5432/chatbot_db")
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            with connection.begin():
                logger.info("Enabling required DB extensions: pg_trgm, vector...")
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("Extensions enabled successfully.")
            
            logger.info("Creating all tables from models...")
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created successfully.")
            
    except Exception as e:
        logger.error(f"Failed during database setup: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()