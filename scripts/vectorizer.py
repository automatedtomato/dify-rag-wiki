import gc
import os
import sys
from logging import getLogger

import torch
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

sys.path.append(os.getcwd())

from sentence_transformers import SentenceTransformer

from backend.app.models import Article

from scripts.common.log_setting import setup_logger

# from sqlalchemy.orm import Session


# ========== Logging Config ==========
logger = getLogger(__name__)
logger = setup_logger(logger=logger)


# ========== Constants ==========
# Download pretrained multilingual model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 128
INTERVAL = BATCH_SIZE * 40
device = "cuda" if torch.cuda.is_available() else "cpu"


# ========== Functions ==========
def main():
    logger.info(f"Vectorize articles with model: {MODEL_NAME}")

    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.error("Database URL is not set.")
        sys.exit(1)

    engine = create_engine(db_url)
    SessionLocal_script = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Load model
    logger.info(f"Using device: {device}")
    model = SentenceTransformer(MODEL_NAME, device=device)
    logger.info("Model loaded.")

    with SessionLocal_script() as db:
        logger.info("Processing articles in batches by primary key...")

        min_id, mx_id = db.query(func.min(Article.id), func.max(Article.id)).one()

        if not min_id:
            logger.error("Database is empty.")
            sys.exit(1)

        logger.info(f"Processing articles from ID {min_id} to {mx_id}")

        total_processed_count = 0
        since_last_commit = 0

        with tqdm(total=(mx_id - min_id) + 1, desc="Vectorizing articles") as pbar:

            for offset in range(0, mx_id - min_id + 1, BATCH_SIZE):
                current_id_start = min_id + offset

                articles_batch = (
                    db.query(Article)
                    .filter(
                        Article.id >= current_id_start,
                        Article.id < current_id_start + BATCH_SIZE,
                    )
                    .all()
                )

                if not articles_batch:
                    pbar.update(BATCH_SIZE)
                    continue

                articles_to_process = [
                    a for a in articles_batch if a.content_vector is None
                ]

                if not articles_to_process:
                    pbar.update(len(articles_batch))
                    continue

                contents = [article.content for article in articles_to_process]

                vectors_tensor = model.encode(
                    contents,
                    show_progress_bar=False,
                    batch_size=32,
                    device=device,
                    convert_to_tensor=True,
                )

                vectors_numpy = vectors_tensor.cpu().numpy()

                for article, vector in zip(articles_to_process, vectors_numpy):
                    article.content_vector = vector

                since_last_commit += len(articles_to_process)
                total_processed_count += len(articles_to_process)
                pbar.update(len(articles_batch))

                # Commit every INTERVAL
                if since_last_commit >= INTERVAL:
                    logger.info(f"Committing {since_last_commit} articles to DB...")
                    db.commit()
                    logger.info("Committed...")
                    since_last_commit = 0
                    
                del vectors_tensor, vectors_numpy, contents, articles_to_process, articles_batch
                # Release GPU memory
                if device == 'cuda':
                    torch.cuda.empty_cache()
                # Force garbage collection
                gc.collect()

            if since_last_commit > 0:
                logger.info(f"Committing final {since_last_commit} articles to DB...")
                db.commit()
                logger.info("Committed...")

        logger.info(
            f"Vectorizing completed. Total articles processed: {total_processed_count}"
        )


if __name__ == "__main__":
    main()
