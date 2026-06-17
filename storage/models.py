from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Additional models for future extensions
class Theme(Base):
    __tablename__ = "theme"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

class SentimentScore(Base):
    __tablename__ = "sentiment"
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)  # VADER compound * 1000 as int
    label = Column(String(20), nullable=False)  # positive/neutral/negative

class InitiativeLink(Base):
    __tablename__ = "initiative_link"
    id = Column(Integer, primary_key=True, index=True)
    theme_id = Column(Integer, nullable=False)
    initiative_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
