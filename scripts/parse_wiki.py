"""
Parse Wikipedia articles .bz2 data.
"""

import bz2
import os
import xml.etree.ElementTree as ET
from logging import INFO, Formatter, StreamHandler, getLogger

# # ========== Logging Config ==========
FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


# ========== Constants ==========
FILE_PATH = os.path.join("data/raw", "jawiki-latest-pages-articles.xml.bz2")

# Namespace of XML
XML_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.10/}"


# ========== Parse functions ==========
def parse_and_save():
    """
    Parse huge Wikipedia article dump in chunks and save to DB.
    """
    logger.info(f"Parsing Wikipedia data from {FILE_PATH}")

    # Unzip .bz2 file in stream
    with bz2.open(FILE_PATH, "rt", encoding="utf-8") as f:
        # `interparse` load XML data in chunks and return elememnt when an event occurs
        # "end" event occurs when </page> tag is reached
        context = ET.interparse(f, events=("end",))

        for event, elem in context:
            # Head of tag contains namespace
            tag = elem.tag.replace(XML_NAMESPACE, "")

            if tag == "page":
                # Extract title
                title_elem = elem.find(f"./{XML_NAMESPACE}title")
                # Return revision/text element
                text_elem = elem.find(f"./{XML_NAMESPACE}revision/{XML_NAMESPACE}text")

                if title_elem is not None and text_elem is not None:
                    title = title_elem.text
                    # text = text_elem.text
                    logger.info(f"Article found: {title}")

                elem.clear()  # IMPOPORTANT: Free memory

    logger.info("Parsing complete.")


if __name__ == "__main__":
    parse_and_save()
