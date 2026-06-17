# feedback_agent/scheduler/job_runner.py
from apscheduler.schedulers.background import BackgroundScheduler
from storage.database import SessionLocal, init_db
from storage.models import Feedback, Theme, SentimentScore, InitiativeLink
from nlp.theme_extractor import extract_themes
from nlp.sentiment_analyzer import analyse_sentiment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_new_feedback():
    db = SessionLocal()
    try:
        # Grab feedback that hasn't been processed yet
        new_items = db.query(Feedback).filter(Feedback.id.notin_(
            db.query(SentimentScore.feedback_id)
        )).all()

        if not new_items:
            logger.info("No new feedback to process.")
            return

        texts = [fb.content for fb in new_items]
        ids   = [fb.id for fb in new_items]

        # --- Sentiment ---
        sentiment_results = analyse_sentiment(texts)
        for fid, (score, label) in zip(ids, sentiment_results):
            db.add(SentimentScore(feedback_id=fid, score=int(score*1000), label=label))

        # --- Theme extraction (simple clustering) ---
        themes = extract_themes(texts)
        for theme_name, idxs in themes:
            # Create / get a Theme entry
            theme_obj = db.query(Theme).filter_by(name=theme_name).first()
            if not theme_obj:
                theme_obj = Theme(name=theme_name, description=None)
                db.add(theme_obj)
                db.flush()  # assign an id

            # Link each feedback in the cluster to the theme
            for i in idxs:
                db.add(InitiativeLink(
                    theme_id=theme_obj.id,
                    initiative_name="TODO: map later",
                    description=None
                ))
        db.commit()
        logger.info("Processed %d feedback items.", len(new_items))
    except Exception as e:
        db.rollback()
        logger.exception("Error during feedback processing: %s", e)
    finally:
        db.close()

def start_scheduler():
    init_db()   # make sure tables exist
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_new_feedback, "interval", hours=1, id="feedback_job")
    scheduler.start()
    logger.info("APScheduler started – hourly job scheduled.")
