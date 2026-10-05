import os
import re
import sys

import search

SECURITY = r"hack|breach|unauthori[sz]ed|compromis|stolen|phishing|leaked"
MONEY_DISPUTE = (
    r"(want|need|request|get|give|issue).{0,15}refund|refund (my|me|the)"
    r"|money back|chargeback|charged twice|double charge|overcharged"
)
LEGAL = r"lawyer|legal action|lawsuit|\bsue\b"
ANGRY = r"furious|angry|unacceptable|terrible|worst|ridiculous|disgusted|fed up|!!"
URGENT = r"urgent|asap|immediately|outage|production|cannot work|can't work|locked out"
BUG = r"\bbug\b|error|crash|broken|not working|doesn't work|fails|failed"
FEATURE = r"feature request|would be nice|please add|wish (you|it)|can you add|add support"


def _has(pattern, text):
    return re.search(pattern, text, re.IGNORECASE) is not None


def triage(text):
    text = text.strip()
    best = search.search(text, top_k=1)[0]
    default_threshold = "0.25" if search.is_mock() else "0.65"
    threshold = float(os.getenv("CONFIDENCE_THRESHOLD", default_threshold))
    confidence = best["score"]

    security = _has(SECURITY, text)
    money = _has(MONEY_DISPUTE, text)
    legal = _has(LEGAL, text)
    angry = _has(ANGRY, text)
    urgent = _has(URGENT, text)

    if security:
        category = "security"
    elif money:
        category = "billing"
    elif _has(BUG, text):
        category = "bug_report"
    elif _has(FEATURE, text):
        category = "feature_request"
    elif confidence >= threshold:
        category = best["category"]
    else:
        category = "other"

    if security:
        priority = "urgent"
    elif urgent or legal:
        priority = "high"
    elif angry or money or category == "bug_report":
        priority = "medium"
    else:
        priority = "low"

    reasons = []
    if security:
        reasons.append("Possible security issue")
    if money:
        reasons.append("Refund or billing dispute needs the billing team")
    if legal:
        reasons.append("Legal language")
    if confidence < threshold:
        reasons.append("No confident match in the knowledge base")

    escalated = len(reasons) > 0
    return {
        "category": category,
        "priority": priority,
        "angry": angry,
        "confidence": confidence,
        "status": "escalated" if escalated else "auto_answered",
        "reasons": reasons,
        "answer": None if escalated else best["content"],
        "source": None if escalated else best["title"],
        "summary": text[:120],
    }


if __name__ == "__main__":
    ticket = " ".join(sys.argv[1:]) or "How do I reset my password?"
    for key, value in triage(ticket).items():
        print(f"{key}: {value}")