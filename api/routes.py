from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from storage.database import get_db
from storage.models import Theme, SentimentScore, Feedback
from sqlalchemy import func

router = APIRouter()

@router.get("/themes")
def get_top_themes(limit: int = 10, db: Session = Depends(get_db)):
    """Return a list of themes with optional placeholder count.
    In a full implementation you would join with feedback entries; here we just return the theme name.
    """
    themes = db.query(Theme).order_by(Theme.id.desc()).limit(limit).all()
    # Placeholder count – could be replaced with real stats later
    return [{"name": t.name, "description": t.description, "count": 0} for t in themes]

@router.get("/sentiment")
def get_sentiment_trends(db: Session = Depends(get_db)):
    """Average sentiment per day (based on Feedback.created_at)."""
    # Compute daily average of the integer score (compound*1000) and convert back
    averages = (
        db.query(func.date_trunc('day', Feedback.created_at).label('day'),
                 func.avg(SentimentScore.score).label('avg_score'))
        .join(SentimentScore, SentimentScore.feedback_id == Feedback.id)
        .group_by('day')
        .order_by('day')
        .all()
    )
    return [{"day": str(day), "avg_score": float(avg)} for day, avg in averages]

@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    """Simple dynamic search endpoint.
    Generates placeholder results that incorporate the query string.
    Also provides a `reviews` list and `reviewCount` for each result
    so the front‑end can display review information.
    """
    import random
    # Generate a few dummy results based on the query
    dummy = []
    for i in range(3):
        # Random number of reviews (0‑5)
        review_count = random.randint(0, 5)
        reviews = [f"Review {j+1}" for j in range(review_count)]
        dummy.append({
            "title": f"{q.title()} Result {i+1}",
            "source": "example.com",
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "price": round(random.uniform(10, 200), 2),
            "reviews": reviews,
            "reviewCount": review_count,
            "metadata": {},
        })
    return {"results": dummy}
