import logging
from logging import Formatter, StreamHandler

FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"


def setup_logger(logger: logging.Logger):
    logger.setLevel(logging.INFO)

    st_handler = StreamHandler()
    formatter = Formatter(FORMAT)
    st_handler.setFormatter(formatter)
    logger.addHandler(st_handler)

    return logger
