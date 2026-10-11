from typing import Any, Dict, List


def combine_hybrid_results(
    semantic_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
    alpha: float = 0.7,
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion / linear score combination between semantic
    and keyword search candidates.
    """
    seen = {}
    for r in semantic_results:
        cid = r.get("chunk_id") or r.get("point_id")
        seen[cid] = dict(r)
        seen[cid]["combined_score"] = r.get("score", 0.0) * alpha

    for r in lexical_results:
        cid = r.get("chunk_id") or r.get("point_id")
        if cid in seen:
            seen[cid]["combined_score"] += r.get("score", 0.0) * (1.0 - alpha)
        else:
            seen[cid] = dict(r)
            seen[cid]["combined_score"] = r.get("score", 0.0) * (1.0 - alpha)

    return sorted(seen.values(), key=lambda x: x["combined_score"], reverse=True)
