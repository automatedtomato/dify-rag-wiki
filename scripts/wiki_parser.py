"""
This script reads the large Wikipedia XML dump and converts it into a more manageable JSON Lines format.
It does not interact with the database.
"""

import bz2
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET

from tqdm import tqdm

sys.path.append(os.getcwd())

from scripts.common.log_setting import setup_logger

# --- Logger Setup ---
logger = logging.getLogger(__name__)
logger = setup_logger(logger=logger)

# --- Constants ---
XML_FILE_PATH = os.path.join(
    "data/raw",
    "jawiki-latest-pages-articles.xml.bz2"
    )
OUTPUT_JSONL_PATH = os.path.join("data/raw", "articles.jsonl")
XML_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.11/}"
# Prefixes for meta-pages to skip
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


def main():
    """
    Parses the Wikipedia XML dump and writes article data to a JSON Lines file.
    """
    logger.info(f"Starting to parse {XML_FILE_PATH} -> {OUTPUT_JSONL_PATH}")

    article_count = 0
    try:
        with bz2.open(XML_FILE_PATH, "rt", encoding="utf-8") as f_in, open(
            OUTPUT_JSONL_PATH, "w", encoding="utf-8"
        ) as f_out:

            context = ET.iterparse(f_in, events=("end",))

            for _, elem in tqdm(context, desc="Parsing XML to JSONL"):
                # Use split to handle namespace gracefully
                tag = elem.tag.split("}", 1)[-1]

                if tag == "page":
                    title_elem = elem.find(f"./{XML_NAMESPACE}title")
                    id_elem = elem.find(f"./{XML_NAMESPACE}id")
                    text_elem = elem.find(
                        f"./{XML_NAMESPACE}revision/{XML_NAMESPACE}text"
                    )

                    # Robustness check
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

                        # Skip redirect pages and meta-pages
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
                        # Write a JSON object as a single line
                        f_out.write(json.dumps(article_data, ensure_ascii=False) + "\n")
                        article_count += 1

                    # Free up memory (crucial)
                    elem.clear()

        logger.info(
            f"Parsing complete. {article_count} articles written to {OUTPUT_JSONL_PATH}"
        )
    except FileNotFoundError:
        logger.error(
            f"Input file not found: {XML_FILE_PATH}. Please run the download script first."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
