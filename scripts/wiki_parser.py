# scripts/parser.py
"""
This script reads the large Wikipedia XML dump and converts it into a more manageable JSON Lines format.
It can process a limited number of articles for testing purposes if ARTICLE_LIMIT is set.
"""

import bz2
import json
import os
import sys
import xml.etree.ElementTree as ET
from logging import getLogger

from tqdm import tqdm

from scripts.common.log_setting import setup_logger

# --- Logger Setup ---
logger = getLogger(__name__)
logger = setup_logger(logger=logger)

# --- Constants ---
XML_FILE_PATH = os.path.join("data/raw", "jawiki-latest-pages-articles.xml.bz2")
OUTPUT_JSONL_PATH = os.path.join("data/raw", "articles.jsonl")
XML_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.11/}"
SKIP_PREFIXES = (
    "Wikipedia:",
    "Help:",
    "Template:",
    "Portal:",
    "プロジェクト:",
    "ノート:",
    "ファイル:",
    "カテゴリ:",
)

# To process all articles, set this to None or comment it out.
# For testing, set it to a number e.g., 50000.
ARTICLE_LIMIT = 10000


def main():
    """
    Parses the Wikipedia XML dump and writes article data to a JSON Lines file.
    """
    if ARTICLE_LIMIT:
        logger.info(f"STARTING PARSE (TEST MODE: First {ARTICLE_LIMIT} articles)")
    else:
        logger.info("STARTING PARSE (FULL RUN)")

    logger.info(f"Input: {XML_FILE_PATH}")
    logger.info(f"Output: {OUTPUT_JSONL_PATH}")

    article_count = 0
    try:
        with bz2.open(XML_FILE_PATH, "rt", encoding="utf-8") as f_in, open(
            OUTPUT_JSONL_PATH, "w", encoding="utf-8"
        ) as f_out:

            context = ET.iterparse(f_in, events=("end",))

            for _, elem in tqdm(context, desc="Parsing XML to JSONL"):
                tag = elem.tag.split("}", 1)[-1]

                if tag == "page":
                    title_elem = elem.find(f"./{XML_NAMESPACE}title")
                    id_elem = elem.find(f"./{XML_NAMESPACE}id")
                    text_elem = elem.find(
                        f"./{XML_NAMESPACE}revision/{XML_NAMESPACE}text"
                    )

                    if (
                        id_elem is not None
                        and id_elem.text
                        and title_elem is not None
                        and title_elem.text
                        and text_elem is not None
                        and text_elem.text
                    ):

                        title = title_elem.text
                        text = text_elem.text

                        if title.startswith(
                            SKIP_PREFIXES
                        ) or text.strip().upper().startswith("#REDIRECT"):
                            elem.clear()
                            continue

                        article_data = {
                            "wiki_id": int(id_elem.text),
                            "title": title,
                            "content": text,
                        }
                        f_out.write(json.dumps(article_data, ensure_ascii=False) + "\n")
                        article_count += 1

                    elem.clear()

                if ARTICLE_LIMIT and article_count >= ARTICLE_LIMIT:
                    logger.info(
                        f"Reached article limit of {ARTICLE_LIMIT}. Stopping parser."
                    )
                    break

        logger.info(
            f"Parsing complete. {article_count} articles written to {OUTPUT_JSONL_PATH}"
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
