# feedback_agent/data_ingestion_service/api/routes.py
"""FastAPI API routes for the dashboard.
Provides two minimal endpoints used by the frontend:
* GET /api/themes – returns a list of theme names and a placeholder count.
* GET /api/sentiment – returns daily average sentiment scores (compound * 1000).
These endpoints are deliberately simple so the UI can at least render without errors.
You can extend them later to include real counts and richer analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from storage.database import get_db
from storage.models import Theme, SentimentScore, Feedback

router = APIRouter()

@router.get("/themes")
def get_themes(db: Session = Depends(get_db)):
    """Return all stored themes.
    Currently each theme is returned with a dummy ``count`` of 0 because the
    linking between feedback and themes is not yet implemented.
    """
    themes = db.query(Theme).all()
    return [{"name": t.name, "count": 0} for t in themes]

@router.get("/sentiment")
def get_sentiment(db: Session = Depends(get_db)):
    """Return daily average sentiment scores.
    The ``score`` column stores VADER's compound value multiplied by 1000.
    We join with ``Feedback`` to get the date of each entry.
    """
    # Join SentimentScore with Feedback to obtain the creation date.
    results = (
        db.query(
            func.date(Feedback.created_at).label("day"),
            func.avg(SentimentScore.score).label("avg_score"),
        )
        .join(Feedback, SentimentScore.feedback_id == Feedback.id)
        .group_by(func.date(Feedback.created_at))
        .order_by(func.date(Feedback.created_at))
        .all()
    )
    # Convert date objects to ISO strings for the frontend.
    return [
        {"day": str(day), "avg_score": int(avg_score)}
        for day, avg_score in results
    ]

@router.post("/run-scheduler")
def run_scheduler():
    from data_ingestion_service.scheduler.job_runner import process_new_feedback
    process_new_feedback()
    return {"detail": "Scheduler executed"}

