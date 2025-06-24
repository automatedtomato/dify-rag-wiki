import logging
import os
import sys
from argparse import ArgumentParser
from logging import Formatter, StreamHandler, getLogger

sys.path.append(os.getcwd())

from create_indexes import create_gin_indexes
from download_wiki import download_wiki
from parse_wiki import parse_and_save
from vectorize_articles import vectorize_and_save

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
    download: bool = True,
    parse: bool = True,
    create_id: bool = True,
    vectorize: bool = True,
):

    logger.info("===== Start Initial Pipeline =====")

    try:
        if download:
            logger.info("==== Downloading Wikipedia data ====")
            download_wiki()

        if parse:
            logger.info("==== Parsing Wikipedia data ====")
            parse_and_save()

        if create_id:
            logger.info("==== Creating GIN indexes ====")
            create_gin_indexes()

        if vectorize:
            logger.info("==== Vectorizing articles data ====")
            vectorize_and_save()

        logger.info("===== Pipeline completed successfully =====")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}\nStop pipeline.", exc_info=True)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "--dl",
        action="store_true",
        help="Download Wikipedia data",
        default=False,
    )

    parser.add_argument(
        "--parse",
        action="store_true",
        help="Parse Wikipedia data",
        default=False,
    )

    parser.add_argument(
        "--id",
        action="store_true",
        help="Create GIN indexes",
        default=False,
    )

    parser.add_argument(
        "--vector",
        action="store_true",
        help="Vectorize Wikipedia data",
        default=False,
    )

    args = parser.parse_args()

    run_pipeline(
        download=args.dl, parse=args.parse, create_id=args.id, vectorize=args.vector
    )
