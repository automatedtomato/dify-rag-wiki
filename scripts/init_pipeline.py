import logging
import os
import sys
from argparse import ArgumentParser
from logging import Formatter, StreamHandler, getLogger

sys.path.append(os.getcwd())

from index_generator import main as create_gin_indexes
from sql_importer import main as import_sql
from title_generator import main as generate_title
from vectorizer import main as vectorize_wiki
from wiki_loader import download_file, download_metadata
from wiki_parser import main as parse_wiki

# ========== Logging Config ==========
FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
st_handler = StreamHandler()
formatter = Formatter(FORMAT)
st_handler.setFormatter(formatter)
logger.addHandler(st_handler)


# ========== Run pipeline ==========
def run_pipeline(
    download_dumps: bool = True,
    download_meta: bool = True,
    parse: bool = True,
    vectorize: bool = True,
    create_id: bool = True,
):

    logger.info("===== Start Initial Pipeline =====")

    try:
        if download_dumps:
            logger.info("==== Downloading Wikipedia data ====")
            download_file()

        if download_meta:
            logger.info("==== Downloading Wikipedia metadata ====")
            download_metadata()

            logger.info("==== Importing SQL files ====")
            import_sql()

            logger.info("==== Generating title ====")
            generate_title()

        if parse:
            logger.info("==== Parsing Wikipedia data ====")
            parse_wiki()

        if vectorize:
            logger.info("==== Vectorizing articles data ====")
            vectorize_wiki()

        if create_id:
            logger.info("==== Creating GIN indexes ====")
            create_gin_indexes()

        logger.info("===== Pipeline completed successfully =====")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}\nStop pipeline.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "--ndl",
        "--no-dl",
        action="store_false",
        help="Not downloading Wikipedia dumps",
        default=True,
    )

    parser.add_argument(
        "--nm",
        "--no-meta",
        action="store_false",
        help="Not downloading Wikipedia metadata",
        default=True,
    )

    parser.add_argument(
        "--np",
        "--no-parse",
        action="store_false",
        help="Not parsing Wikipedia data",
        default=True,
    )

    parser.add_argument(
        "--nv",
        "--vector",
        action="store_false",
        help="Not vectorize Wikipedia data",
        default=True,
    )

    parser.add_argument(
        "--nid",
        "--no-id",
        action="store_false",
        help="Not create GIN indexes",
        default=True,
    )

    args = parser.parse_args()

    run_pipeline(
        download_dumps=args.ndl,
        download_meta=args.nm,
        parse=args.np,
        vectorize=args.nv,
        create_id=args.nid,
    )
