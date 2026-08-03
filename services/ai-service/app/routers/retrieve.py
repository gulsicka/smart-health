from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, auth, embedder, models
from app.database import get_db

router = APIRouter()


@router.post("/retrieve", response_model=schemas.RetrieveResponse)
def retrieve(
    body: schemas.RetrieveRequest,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(auth.get_current_user),
):
    query_vector = embedder.embed(body.query)
    distance = models.DocumentChunk.embedding.l2_distance(query_vector).label("score")

    results = (
        db.query(models.DocumentChunk, distance)
        .order_by(distance)
        .limit(body.top_k)
        .all()
    )

    output = [
        schemas.RetrieveResult(content=row.content, source=row.source, score=round(score, 6))
        for row, score in results
    ]
    return schemas.RetrieveResponse(results=output)
