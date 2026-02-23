
# -------------------------
# Validation helpers
# -------------------------
def _normalize_sq(s: str) -> str:
    return " ".join(s.strip().split())


def _dedupe_keep_order(items):
    seen = set()
    out = []
    for x in items:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out

def _validate_sub_queries(sub_queries, fallback_query: str):
    if not isinstance(sub_queries, list):
        return [fallback_query]

    cleaned = []
    for s in sub_queries:
        if isinstance(s, str):
            s = _normalize_sq(s)
            if s:
                cleaned.append(s)

    cleaned = _dedupe_keep_order(cleaned)

    # Enforce 2–5 strictly, but safe fallback
    if len(cleaned) < 2:
        return [fallback_query]
    if len(cleaned) > 5:
        cleaned = cleaned[:5]

    return cleaned