import os
import sys
from logging import INFO, Formatter, StreamHandler, getLogger

from tqdm import tqdm

sys.path.append(os.getcwd())

from sentence_transformers import SentenceTransformer
# from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Article

# ========== Logging Config ==========
FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"

logger = getLogger(__name__)
logger.setLevel(INFO)

st_handler = StreamHandler()

formatter = Formatter(FORMAT)

st_handler.setFormatter(formatter)

logger.addHandler(st_handler)


# ========== Constants ==========
# Download pretrained multilingual model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32


# ========== Functions ==========
def vectorize_and_save():
    logger.info(f"Vectorize articles with model: {MODEL_NAME}")

    # Load model
    model = SentenceTransformer(MODEL_NAME)

    with SessionLocal() as db:
        # Get total number of articles
        total_articles_to_process = (
            db.query(Article).filter(Article.content_vector is None).count()
        )

        logger.info(f"Total articles to process: {total_articles_to_process}")

        if total_articles_to_process == 0:
            logger.info("All articles are already vectorized.")
            return

        with tqdm(total=total_articles_to_process, desc="Vectorizing articles") as pbar:
            # User offset to process in batches
            offset = 0

            while offset < total_articles_to_process:
                # Get batch of articles
                articles_batch = (
                    db.query(Article)
                    .filter(Article.content_vector is None)
                    .limit(BATCH_SIZE)
                    .all()
                )

                if not articles_batch:
                    break  # if batch is empty, break loop

                # Extranct content as list
                contents = [article.content for article in articles_batch]

                # Vectorize contents using the model
                logger.info(f"Vectorizing {len(contents)} articles...")
                vectors = model.encode(contents, show_progress_bar=False)

                # Set the vector to each article and refresh
                for article, vector in zip(articles_batch, vectors):
                    article.content_vector = vector

                db.commit()

                offset += len(articles_batch)
                pbar.update(len(articles_batch))

        logger.info(
            f"Vectorizing completed. {total_articles_to_process} articles processed."
        )


if __name__ == "__main__":
    vectorize_and_save()
