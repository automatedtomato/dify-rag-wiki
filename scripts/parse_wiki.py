"""
Parse Wikipedia articles .bz2 data.
"""

import bz2
import logging
import os
import sys
import xml.etree.ElementTree as ET
from logging import Formatter, StreamHandler, getLogger
from pathlib import Path

import sqlalchemy
from tqdm import tqdm

# Add backend directory to sys.path
cur = Path(__file__)
root = cur.parents[1]
sys.path.append(str(root))

from backend.app.database import SessionLocal, engine
from backend.app.models import Article, Base

# # ========== Logging Config ==========
FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


# ========== Constants ==========
FILE_PATH = os.path.join(
    "data/raw",
    # "jawiki-latest-pages-articles.xml.bz2" # Japanese
    "enwiki-latest-pages-articles.xml.bz2",  # English
)

# Namespace of XML
XML_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.11/}"


TARGET_CATEGORIES = {"Category:Dinosaurs", "Category:Paleontology", "Category:Mesozoic"}

# Prefixes to skip
SKIP_PREFIXES = (
    "File:",
    "Category:",
    "Template:",
    "Wikipedia:",
    "Help:",
    "Portal:",
    "ファイル:",
    "カテゴリ:",
    "テンプレート:",
    "プロジェクト:",
    "ヘルプ:",
    "ノート:",
)


# ========== Parse functions ==========
def main():
    """
    Parse huge Wikipedia article dump in chunks and save to DB.
    """
    logger.info(f"Parsing Wikipedia data from {FILE_PATH}")

    article_buffer = []
    BATCH_SIZE = 1000
    article_count = 0

    with SessionLocal() as db:
        try:
            # Step 1: Enable extensions
            logger.info("Enabling extensions...")
            # Check pg_trgm extension
            db.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            # Check pg_vector extension
            db.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector;"))
            db.commit()
            logger.info("Extensions enabled.")
        except Exception as e:
            logger.error(f"Failed to enable extensions: {e}")
            db.rollback()
            return

        # Step 2: Create tables
        logger.info("Creating tables...")
        try:
            # Create tables
            Base.metadata.create_all(bind=engine)
            logger.info("Tables are ready.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            db.rollback()
            return

        # Step 3: Clean up DB
        logger.info("Clean up DB...")
        try:
            # Delete all articles
            num_deleted = db.query(Article).delete()
            db.commit()
            if num_deleted > 0:
                logger.info(f"Deleted {num_deleted} articles")
            else:
                logger.info("No articles to delete. DB is clean.")
        except Exception as e:
            logger.error(f"Failed to clean up DB: {e}")
            db.rollback()
            return

        # Step 4: Unzip .bz2 file in stream
        article_buffer = []
        BATCH_SIZE = 1000
        article_count = 0

        saved = 0

        with bz2.open(FILE_PATH, "rt", encoding="utf-8") as f:
            # `iterparse` load XML data in chunks and
            # return elememnt when an event occurs
            # "end" event occurs when </page> tag is reached
            context = ET.iterparse(f, events=("end",))

            logger.info(
                f"Start parsing XML data. Target Category: {TARGET_CATEGORIES}..."
            )

            for event, elem in tqdm(context):

                # Head of tag contains namespace
                tag = elem.tag.replace(XML_NAMESPACE, "")

                if tag == "page":
                    # Extract article info
                    title_elem = elem.find(f"./{XML_NAMESPACE}title")  # title
                    id_elem = elem.find(f"./{XML_NAMESPACE}id")  # id
                    text_elem = elem.find(
                        f"./{XML_NAMESPACE}revision/{XML_NAMESPACE}text"
                    )  # text

                    if (
                        title_elem is not None
                        and id_elem is not None
                        and text_elem is not None
                        and text_elem.text
                    ):
                        title = title_elem.text
                        text = text_elem.text
                        wiki_id = id_elem.text

                        # Check if article is in target category
                        if not any(f"[[{cat}]]" in text for cat in TARGET_CATEGORIES):
                            elem.clear()
                            continue

                        # Skip articles with the prefixes
                        if title.startswith(
                            SKIP_PREFIXES
                        ) or text.strip().upper().startswith("#REDIRECT"):
                            elem.clear()
                            continue

                        # Create article object and add to buffer
                        new_article = Article(
                            wiki_id=wiki_id,
                            title=title,
                            content=text,
                        )
                        article_buffer.append(new_article)
                        article_count += 1
                        saved += 1

                        # If buffer is full, save to DB
                        if len(article_buffer) >= BATCH_SIZE:
                            db.add_all(article_buffer)
                            db.commit()
                            logger.info(f"Saved {len(article_buffer)} articles to DB")
                            article_buffer = []

                    elem.clear()  # IMPOPORTANT: Free memory

        if article_buffer:
            db.add_all(article_buffer)
            db.commit()
            logger.info(f"Saved {len(article_buffer)} remaining articles to DB")

        logger.info(f"Parsing complete. {article_count} articles saved to DB")


if __name__ == "__main__":
    main()
