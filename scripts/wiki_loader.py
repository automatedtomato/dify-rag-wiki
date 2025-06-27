"""
Download Wikipedia articles and metadata from dumps.
"""

import os
import gzip
import shutil
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
DUMP_FILES = {
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


# ========== Downloader ==========
def download_file(url: str, save_path: str):
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

def main(lang: str = "en"):
    os.makedirs(SAVE_DIR, exist_ok=True)
    for name, url in DUMP_FILES[lang].items():
        file_name = url.split("/")[-1]
        save_path = os.path.join(SAVE_DIR, file_name)
        
        if os.path.exists(save_path.replace(".gz", ".sql")):
            logger.warning(f"{save_path} already exists. Skipping.")
            continue
        
        if not os.path.exists(save_path):
            logger.info(f"Downloading dump: {name}")
            download_file(url, save_path)
            
        logger.info(f"Unzipping {save_path}...")
        with gzip.open(save_path, "rb") as f_in:
            with open(save_path.replace(".gz", ".sql"), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info(f"Unzipping complete.")
        
if __name__ == "__main__":
    main()