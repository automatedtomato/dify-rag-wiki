"""
Download Wikipedia articles and metadata from dumps.
"""

import os
from logging import getLogger

import requests
from tqdm import tqdm

from scripts.common.log_setting import setup_logger

# ========== Logging Config ==========
logger = getLogger(__name__)
logger = setup_logger(logger=logger)


# ========== Constatns ==========

DUMP_FILES = {
    "en": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2",
    "ja": "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles.xml.bz2",
}

METADATA_FILES = {
    "en": {
        "page": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page.sql.gz",
        "category_links": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-categorylinks.sql.gz",
    },
    "ja": {
        "page": "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles.sql.gz",
        "category_links": "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-categorylinks.sql.gz",
    },
}


SAVE_DIR = "data/raw"
SAVE_PATH = os.path.join(SAVE_DIR, "jawiki-latest-pages-articles.xml.bz2")


# ========== Downloader ==========
def main(save_path: str = SAVE_PATH, url: str = DUMP_FILES["ja"]):
    """
    Stream-download Wikipedia articles data from dumps.
    Show progress bar.
    """
    logger.info(f"Downloading Wikipedia data from {url}")
    logger.info(f"Saving to {save_path}")

    os.makedirs(SAVE_DIR, exist_ok=True)

    try:
        # Set "stream=True" to load  the file in chunks
        with requests.get(url, stream=True) as r:
            r.raise_for_status()  # Raise exception for HTTP errors

            # Get total size of the file
            total_size_in_bytes = int(r.headers.get("content-length", 0))
            block_size = 1024  # 1 KB

            # Show progress bar
            progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)

            # Load file with binary mode
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=block_size):
                    progress_bar.update(len(chunk))
                    f.write(chunk)

            progress_bar.close()

            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                logger.error("Incomplete download. Check the file size and URL.")
            else:
                logger.info("Download complete.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading Wikipedia data: {e}")


if __name__ == "__main__":
    main()
