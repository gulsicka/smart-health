from sqlalchemy.orm import Session
from app import models, embedder


def get_existing_chunk(db: Session, source: str):
    return db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).first()


def delete_chunks(db: Session, source: str):
    db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).delete()
    db.commit()


def ingest_chunks(db: Session, source: str, chunks: list[str], file_hash: str = None):
    for chunk in chunks:
        db.add(models.DocumentChunk(
            source=source,
            content=chunk,
            embedding=embedder.embed(chunk),
            file_hash=file_hash,
        ))
    db.commit()


def retrieve_chunks(db, query, top_k, source_prefix: str = None):
    query_vector = embedder.embed(query)
    distance = models.DocumentChunk.embedding.l2_distance(query_vector).label("score")
    q = db.query(models.DocumentChunk, distance)
    if source_prefix:
        q = q.filter(models.DocumentChunk.source.startswith(source_prefix))
    return q.order_by(distance).limit(top_k).all()
