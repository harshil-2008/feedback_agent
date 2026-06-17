"""Insight computation module.
Takes a list of unified result dicts and returns high‑level analytics:
  - most_mentioned_colors
  - average_price
  - sentiment_distribution
  - top_keywords
"""
import re
from collections import Counter
from typing import List, Dict, Any

# ── Colour Detection ──────────────────────────────────────────────
_COLOUR_NAMES = [
    "red", "blue", "green", "black", "white", "gold", "silver",
    "pink", "purple", "orange", "yellow", "brown", "grey", "gray",
    "navy", "teal", "maroon", "beige", "ivory", "rose", "coral",
    "turquoise", "magenta", "violet", "bronze", "copper", "cream",
    "burgundy", "olive", "khaki", "charcoal", "mint", "lavender",
]
_COLOUR_PATTERN = re.compile(
    r"\b(" + "|".join(_COLOUR_NAMES) + r")\b", re.IGNORECASE
)

# ── Stop‑words (minimal set for keyword extraction) ──────────────
_STOP_WORDS = set(
    "the a an and or but is it in on at to for of with by from as this that "
    "be are was were has have had do does did will would can could shall should "
    "may might must not no so if then than too very just also about more most "
    "all any each every some few many much how what which who whom whose when "
    "where why there here their them they he she him her his its we us our you "
    "your i me my mine myself itself himself herself themselves been being into "
    "over after before between under through during without within along across".split()
)


def compute_insights(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute all insight categories from the aggregated results."""
    return {
        "most_mentioned_colors": _most_mentioned_colors(results),
        "average_price": _average_price(results),
        "sentiment_distribution": _sentiment_distribution(results),
        "top_keywords": _top_keywords(results),
        "total_results": len(results),
        "sources_found": list({r.get("source", "unknown") for r in results}),
    }


def _most_mentioned_colors(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counter: Counter = Counter()
    for r in results:
        text = (r.get("title") or "") + " " + (r.get("snippet") or "")
        matches = _COLOUR_PATTERN.findall(text.lower())
        counter.update(matches)
    return [{"color": c, "count": n} for c, n in counter.most_common(10)]


def _average_price(results: List[Dict[str, Any]]) -> float | None:
    prices = []
    for r in results:
        metrics = r.get("metrics") or {}
        price = metrics.get("price")
        if price is not None:
            try:
                prices.append(float(price))
            except (ValueError, TypeError):
                pass
    if not prices:
        return None
    return round(sum(prices) / len(prices), 2)


def _sentiment_distribution(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Quick rule‑based sentiment bucketing from title text.
    Uses VADER if available, otherwise falls back to a naive
    positive‑word / negative‑word counter.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
    except ImportError:
        analyzer = None

    dist = {"positive": 0, "neutral": 0, "negative": 0}
    for r in results:
        text = (r.get("title") or "") + " " + (r.get("snippet") or "")
        if not text.strip():
            dist["neutral"] += 1
            continue
        if analyzer:
            score = analyzer.polarity_scores(text)["compound"]
        else:
            score = 0.0  # fallback – treat as neutral
        if score >= 0.05:
            dist["positive"] += 1
        elif score <= -0.05:
            dist["negative"] += 1
        else:
            dist["neutral"] += 1
    return dist


def _top_keywords(results: List[Dict[str, Any]], top_n: int = 15) -> List[Dict[str, Any]]:
    counter: Counter = Counter()
    for r in results:
        text = (r.get("title") or "") + " " + (r.get("snippet") or "")
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        words = [w for w in words if w not in _STOP_WORDS]
        counter.update(words)
    return [{"keyword": w, "count": n} for w, n in counter.most_common(top_n)]
