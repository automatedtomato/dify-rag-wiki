import os
import sys
from argparse import ArgumentParser
from itertools import dropwhile
from logging import getLogger

sys.path.append(os.getcwd())

from scripts.common.log_setting import setup_logger
from scripts.index_generator import main as create_indexes
from scripts.inserter import main as insert_to_db
from scripts.setup_db import main as setup_db
from scripts.vectorizer import main as vectorize
from scripts.wiki_loader import main as download_dump
from scripts.wiki_parser import main as parse_dump

logger = getLogger(__name__)
logger = setup_logger(logger=logger)

PROCESS_MAP = {
    "download_dump": download_dump,
    "setup_db": setup_db,
    "parse_dump": parse_dump,
    "insert_to_db": insert_to_db,
    "vectorize": vectorize,
    "create_indexes": create_indexes,
}


def run_pipeline(start_from: str | None = None):

    if start_from is not None and start_from not in PROCESS_MAP:
        raise ValueError(f"Invalid starting point: {start_from}")

    if start_from is None:
        start_from = "setup_db"

    logger.info(f"Starting from: {start_from}")

    steps = PROCESS_MAP.items()
    if start_from is not None:
        steps = dropwhile(lambda x: x[0] != start_from, steps)

    for name, func in steps:
        logger.info(f"Running: {name}")
        try:
            func()
        except Exception as e:
            print(f"Error in step {name}: {e}")
            raise


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--start-from",
        type=str,
        default=None,
        choices=PROCESS_MAP.keys(),
        help="Starting point of the pipeline",
    )
    args = parser.parse_args()
    run_pipeline(start_from=args.start_from)
