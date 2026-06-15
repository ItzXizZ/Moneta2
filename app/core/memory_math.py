#!/usr/bin/env python3
"""
Mathematics of Memory — four-stage strength model.

1. Encoding  — S = S_max × (1 - e^(-r·n))     strength built through repetition
2. Recall    — P(recall) = S_target / ΣS       recall probability; use strengthens S
3. Sleep     — replay + optimization           consolidation locks strength in
4. Forgetting — R = e^(-t/S)                   retention decays; larger S decays slower
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

# Defaults aligned with the presentation model (strength on 0–100 scale)
S_MAX = 100.0
LEARNING_RATE = 0.5  # r — how fast strength builds per repetition
RECALL_WRITE_BOOST = 0.15  # fractional boost toward ceiling on successful recall
SLEEP_HOURS_THRESHOLD = 8.0  # hours of inactivity before consolidation
CONSOLIDATION_REPLAY_FACTOR = 0.25  # replay contribution during sleep


def _parse_timestamp(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace('Z', '+00:00')
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _elapsed_days_since(timestamp: Union[str, datetime, None], now: Optional[datetime] = None) -> float:
    parsed = _parse_timestamp(timestamp)
    if parsed is None:
        return 0.0
    current = now or datetime.now(timezone.utc)
    delta = current - parsed
    return max(0.0, delta.total_seconds() / 86400.0)


def _elapsed_hours_since(timestamp: Union[str, datetime, None], now: Optional[datetime] = None) -> float:
    return _elapsed_days_since(timestamp, now) * 24.0


# ---------------------------------------------------------------------------
# Stage 1 — Encoding
# ---------------------------------------------------------------------------

def encoding_strength(
    repetitions: int,
    s_max: float = S_MAX,
    learning_rate: float = LEARNING_RATE,
) -> float:
    """S = S_max × (1 - e^(-r·n)). Each repetition adds less than the last."""
    n = max(1, int(repetitions))
    return s_max * (1.0 - math.exp(-learning_rate * n))


# ---------------------------------------------------------------------------
# Stage 4 — Forgetting
# ---------------------------------------------------------------------------

def retention(days_since_study: float, strength: float) -> float:
    """R = e^(-t/S). Fraction of memory retained after t days."""
    if strength <= 0:
        return 0.0
    t = max(0.0, days_since_study)
    return math.exp(-t / strength)


def strength_after_forgetting(base_strength: float, days_since_access: float) -> float:
    """Apply the forgetting curve to a stored strength value."""
    if base_strength <= 0:
        return 0.0
    return base_strength * retention(days_since_access, base_strength)


# ---------------------------------------------------------------------------
# Stage 2 — Recall
# ---------------------------------------------------------------------------

def recall_probability(target_strength: float, all_strengths: List[float]) -> float:
    """P(recall) = S_target / ΣS(all memories)."""
    total = sum(max(0.0, s) for s in all_strengths)
    if total <= 0:
        return 0.0
    return max(0.0, target_strength) / total


def reinforce_on_recall(
    current_strength: float,
    repetitions: int,
    s_max: float = S_MAX,
    learning_rate: float = LEARNING_RATE,
) -> tuple[float, int]:
    """
    Recall = read + write. A successful recall adds strength (another encoding step).
    Returns (new_strength, new_repetition_count).
    """
    new_repetitions = max(1, int(repetitions)) + 1
    encoded = encoding_strength(new_repetitions, s_max, learning_rate)
    # Testing effect: active recall gives an extra push toward the ceiling
    headroom = max(0.0, s_max - current_strength)
    boosted = current_strength + headroom * RECALL_WRITE_BOOST
    return min(s_max, max(encoded, boosted)), new_repetitions


# ---------------------------------------------------------------------------
# Stage 3 — Sleep / consolidation
# ---------------------------------------------------------------------------

def consolidate_on_sleep(
    stored_strength: float,
    fragile_strength: float,
    s_max: float = S_MAX,
) -> float:
    """
    Sleep = replay + optimization. Fragile daytime strength is replayed and
    copied into long-term storage, protecting S from full decay.
    """
    if stored_strength <= 0 and fragile_strength <= 0:
        return 0.0
    replay_gain = fragile_strength * CONSOLIDATION_REPLAY_FACTOR
    headroom = max(0.0, s_max - stored_strength)
    optimized = stored_strength + min(headroom, replay_gain)
    return min(s_max, max(stored_strength, optimized, fragile_strength * 0.85))


def needs_sleep_consolidation(
    last_accessed: Union[str, datetime, None],
    now: Optional[datetime] = None,
) -> bool:
    """True when enough idle time has passed for overnight consolidation."""
    return _elapsed_hours_since(last_accessed, now) >= SLEEP_HOURS_THRESHOLD


# ---------------------------------------------------------------------------
# Unified memory strength pipeline
# ---------------------------------------------------------------------------

def compute_effective_strength(
    memory: Dict[str, Any],
    now: Optional[datetime] = None,
    apply_consolidation: bool = True,
) -> float:
    """
    Run the full strength pipeline for one memory:
    stored S → forgetting decay → optional sleep consolidation.
    """
    repetitions = int(memory.get('access_count', 0) or 0)
    stored = float(memory.get('score', 0) or 0)

    if stored <= 0 and repetitions > 0:
        stored = encoding_strength(repetitions)
    elif stored <= 0:
        stored = encoding_strength(1)

    days_idle = _elapsed_days_since(memory.get('last_accessed'), now)
    fragile = strength_after_forgetting(stored, days_idle)

    if apply_consolidation and needs_sleep_consolidation(memory.get('last_accessed'), now):
        return consolidate_on_sleep(stored, fragile)

    return fragile


def compute_all_effective_strengths(
    memories: List[Dict[str, Any]],
    now: Optional[datetime] = None,
) -> List[float]:
    return [compute_effective_strength(m, now) for m in memories]


def initial_memory_state(content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """State for a newly encoded memory (first repetition)."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        'content': content,
        'tags': tags or [],
        'score': encoding_strength(1),
        'access_count': 1,
        'last_accessed': now,
    }


def apply_recall_update(memory: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Strengthen a memory after it was successfully recalled."""
    current = compute_effective_strength(memory, now, apply_consolidation=False)
    repetitions = int(memory.get('access_count', 0) or 1)
    new_score, new_reps = reinforce_on_recall(current, repetitions)
    updated = dict(memory)
    updated['score'] = round(new_score, 4)
    updated['access_count'] = new_reps
    updated['last_accessed'] = (now or datetime.now(timezone.utc)).isoformat()
    return updated


def apply_consolidation_update(memory: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Lock in strength after sleep consolidation."""
    stored = float(memory.get('score', 0) or 0)
    fragile = compute_effective_strength(memory, now, apply_consolidation=False)
    updated = dict(memory)
    updated['score'] = round(consolidate_on_sleep(stored, fragile), 4)
    updated['last_accessed'] = (now or datetime.now(timezone.utc)).isoformat()
    return updated


def rank_memories_for_recall(
    memories: List[Dict[str, Any]],
    query: str,
    limit: int = 10,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Search memories using content overlap weighted by recall probability.
    P(recall) = S_target / ΣS naturally boosts stronger memories.
    """
    if not query.strip() or not memories:
        return []

    query_lower = query.lower()
    query_words = {
        word.strip('.,!?;:')
        for word in query_lower.split()
        if len(word.strip('.,!?;:')) > 2
    }

    effective_strengths = compute_all_effective_strengths(memories, now)
    total_strength = sum(effective_strengths)

    ranked = []
    for memory, eff_strength in zip(memories, effective_strengths):
        content = memory.get('content', '').lower()
        if not content:
            continue

        relevance = 0.0
        if query_lower in content:
            relevance += 1.0
        if query_words:
            matches = sum(1 for w in query_words if w in content)
            relevance += matches / len(query_words)

        if relevance <= 0:
            continue

        recall_p = recall_probability(eff_strength, effective_strengths) if total_strength > 0 else 0.0
        final_score = relevance * 0.6 + recall_p * 0.4

        entry = dict(memory)
        entry['effective_strength'] = round(eff_strength, 4)
        entry['recall_probability'] = round(recall_p, 6)
        entry['search_score'] = round(final_score, 6)
        ranked.append(entry)

    ranked.sort(key=lambda m: m['search_score'], reverse=True)
    return ranked[:limit]
