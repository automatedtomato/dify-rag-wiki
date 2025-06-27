"""
Download Wikipedia articles data from dumps.
"""

import os
from logging import INFO, Formatter, StreamHandler, getLogger

import requests
from tqdm import tqdm

# ========== Logging Config ==========
FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


# ========== Constatns ==========
WIKI_DUMP_URL = (
    # "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles.xml.bz2" # Japanese
    "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2"  # English
)

SAVE_DIR = "data/raw"

FILE_PATH = os.path.join(
    SAVE_DIR,
    # "jawiki-latest-pages-articles.xml.bz2" # Japanese
    "enwiki-latest-pages-articles.xml.bz2",  # English
)


# ========== Download function ==========
def main():
    """
    Stream-download Wikipedia articles data from dumps.
    Show progress bar.
    """
    logger.info(f"Downloading Wikipedia data from {WIKI_DUMP_URL}")
    logger.info(f"Saving to {FILE_PATH}")

    os.makedirs(SAVE_DIR, exist_ok=True)

    try:
        # Set "stream=True" to load  the file in chunks
        with requests.get(WIKI_DUMP_URL, stream=True) as r:
            r.raise_for_status()  # Raise exception for HTTP errors

            # Get total size of the file
            total_size_in_bytes = int(r.headers.get("content-length", 0))
            block_size = 1024  # 1 KB

            # Show progress bar
            progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)

            # Load file with binary mode
            with open(FILE_PATH, "wb") as f:
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
    if os.path.exists(FILE_PATH):
        logger.info(f"{FILE_PATH} already exists. Skipping download.")
    else:
        main()
