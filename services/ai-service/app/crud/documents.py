from sqlalchemy.orm import Session
from app import models, embedder


def get_existing_chunk(db: Session, source: str):
    return db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).first()


def delete_chunks(db: Session, source: str):
    db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source).delete()
    db.commit()
    
def delete_chunks_for_page(db, source, page_number):
    db.query(models.DocumentChunk).filter(models.DocumentChunk.source == source, models.DocumentChunk.page_number == page_number).delete()
    db.commit()


def ingest_chunks(db: Session, source: str, chunks: list[str], page_number: int = None, page_hash: str = None):
    for chunk in chunks:
        db.add(models.DocumentChunk(
            source=source,
            content=chunk,
            embedding=embedder.embed(chunk),
            page_hash=page_hash,
            page_number=page_number
        ))
    db.commit()


def replace_page_chunks(db: Session, source: str, page_number: int, chunks: list[str], page_hash: str): #delete and ingestion in same call
    db.query(models.DocumentChunk).filter(
        models.DocumentChunk.source == source,
        models.DocumentChunk.page_number == page_number,
    ).delete()
    for chunk in chunks:
        db.add(models.DocumentChunk(
            source=source,
            content=chunk,
            embedding=embedder.embed(chunk),
            page_hash=page_hash,
            page_number=page_number,
        ))
    db.commit()


def retrieve_chunks(db, query, top_k, source_prefix: str = None):
    query_vector = embedder.embed(query)
    distance = models.DocumentChunk.embedding.cosine_distance(query_vector).label("score")
    q = db.query(models.DocumentChunk, distance)
    if source_prefix:
        source = models.DocumentChunk.source
        q = q.filter(
            (source == source_prefix)
            | source.startswith(source_prefix + "-")
            | source.endswith("-" + source_prefix)
            | source.contains("-" + source_prefix + "-")
        )
    return q.order_by(distance).limit(top_k).all()

def get_page_hashes(db, source):
    records = db.query(models.DocumentChunk.page_number, models.DocumentChunk.page_hash).distinct().filter(models.DocumentChunk.source == source).all()
    return {r.page_number: r.page_hash for r in records}