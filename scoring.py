from __future__ import annotations

import re
from typing import Set, Tuple, List, Dict, Any

STOPWORDS: Set[str] = {
    "a","an","the","and","or","to","of","in","on","for","with","is","are","was","were",
    "be","been","being","as","at","by","this","that","it","from","you","we","our","your",
    "they","will","can","should","must","plus","role","position","company","team","work",
    "working","looking","opportunity","join","make","impact","support","help","internal",
    "projects","project","use","using","based"
}

def normalize(text: str) -> Set[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\-]+", " ", text)

    tokens: Set[str] = set()
    for t in text.split():
        if t in STOPWORDS:
            continue
        if len(t) <= 2:
            continue
        tokens.add(t)
    return tokens

def keyword_coverage_score(cv_text: str, job_keywords: List[str]) -> Tuple[int, Dict[str, Any]]:
    """
    Score how much CV covers job keywords (10-15 items).
    Returns (score 0..100, debug)
    """
    cv_tokens = normalize(cv_text)

    kw_tokens: Set[str] = set()
    for kw in job_keywords:
        kw_tokens |= normalize(kw)

    if not kw_tokens:
        return 0, {"reason": "Empty keywords after normalization"}

    overlap = cv_tokens.intersection(kw_tokens)
    missing = kw_tokens - cv_tokens
    score = int(round((len(overlap) / len(kw_tokens)) * 100))
    score = max(0, min(score, 100))

    debug = {
        "cv_token_count": len(cv_tokens),
        "keyword_token_count": len(kw_tokens),
        "overlap_count": len(overlap),
        "overlap_examples": sorted(list(overlap))[:20],
        "missing_keywords": sorted(list(missing))[:20],
    }
    return score, debug

def final_score(llm_score: int, keyword_score: int) -> int:
    combined = (0.75 * llm_score) + (0.25 * keyword_score)
    return int(round(max(0, min(combined, 100))))

def decision_from_score(score: int) -> str:
    if score >= 75:
        return "PROCEED"
    if score >= 60:
        return "REVIEW"
    return "REJECT"