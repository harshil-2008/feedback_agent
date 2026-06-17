# feedback_agent/nlp/sentiment_analyzer.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Tuple

_ANALYZER = SentimentIntensityAnalyzer()

def analyse_sentiment(texts: List[str]) -> List[Tuple[float, str]]:
    """
    Returns a list of (compound_score, label) for each text.
    Label mapping:
        compound >= 0.05   → "positive"
        compound <= -0.05  → "negative"
        otherwise         → "neutral"
    """
    results = []
    for t in texts:
        comp = _ANALYZER.polarity_scores(t)["compound"]
        if comp >= 0.05:
            label = "positive"
        elif comp <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        results.append((comp, label))
    return results
