# feedback_agent/nlp/theme_extractor.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List, Tuple

# Load a lightweight multilingual model once (shared across calls)
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts: List[str]) -> np.ndarray:
    """Return a 2‑D numpy array of sentence embeddings."""
    return np.vstack(_MODEL.encode(texts, convert_to_numpy=True))

def cluster_embeddings(embeds: np.ndarray, threshold: float = 0.75) -> List[List[int]]:
    """
    Simple agglomerative clustering based on cosine similarity.
    Returns a list of clusters, each cluster is a list of row indices.
    """
    similarity = util.cos_sim(embeds, embeds).cpu().numpy()
    visited = set()
    clusters = []

    for i in range(len(similarity)):
        if i in visited:
            continue
        # Grab all points similar enough to i (including i itself)
        cluster = [j for j, sim in enumerate(similarity[i]) if sim >= threshold]
        visited.update(cluster)
        clusters.append(cluster)

    return clusters

def extract_themes(texts: List[str]) -> List[Tuple[str, List[int]]]:
    """
    Returns a list of (representative_theme, indices_of_texts) tuples.
    The representative is the first text in each cluster.
    """
    embeds = embed_texts(texts)
    clusters = cluster_embeddings(embeds)
    return [(texts[idxs[0]], idxs) for idxs in clusters]
