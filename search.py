import json
import math
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

KB_PATH = Path(__file__).parent / "knowledge_base.json"
ARTICLES = json.loads(KB_PATH.read_text(encoding="utf-8"))

EMBED_MODEL = "gemini-embedding-001"
STOPWORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "in",
    "is", "it", "my", "of", "on", "or", "the", "to", "we", "what", "you",
    "your", "me", "with", "our", "this", "that", "be", "get",
}

_client = None
_vectors = None


def is_mock():
    return os.getenv("MOCK_MODE", "true").lower() == "true"


def _words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


def _mock_score(question, article):
    q = _words(question)
    if not q:
        return 0.0
    title_hits = len(q & _words(article["title"]))
    body_hits = len(q & _words(article["content"]))
    return (2 * title_hits + body_hits) / (2 * len(q))


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def _embed(texts):
    result = _get_client().models.embed_content(model=EMBED_MODEL, contents=texts)
    return [e.values for e in result.embeddings]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def search(question, top_k=3):
    """Return the best matching articles, highest score first."""
    global _vectors
    if is_mock():
        scores = [_mock_score(question, a) for a in ARTICLES]
    else:
        if _vectors is None:
            _vectors = _embed([a["title"] + ". " + a["content"] for a in ARTICLES])
        q_vec = _embed([question])[0]
        scores = [_cosine(q_vec, v) for v in _vectors]

    ranked = sorted(zip(scores, ARTICLES), key=lambda pair: pair[0], reverse=True)
    return [
        {"id": a["id"], "title": a["title"], "category": a["category"],
         "content": a["content"], "score": round(s, 3)}
        for s, a in ranked[:top_k]
    ]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How do I reset my password?"
    print("Mode:", "mock" if is_mock() else "gemini")
    for hit in search(question):
        print(hit["score"], "-", hit["title"])