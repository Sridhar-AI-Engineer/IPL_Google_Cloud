from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from threading import Lock
from typing import Any


class RuntimeControls:
    def __init__(self):
        self._lock = Lock()
        self._user_events: dict[str, deque[datetime]] = defaultdict(deque)
        self._ai_calls_by_day: dict[date, int] = defaultdict(int)
        self._eval_cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _prune_user_events(self, user_key: str, now: datetime, window: timedelta) -> None:
        events = self._user_events[user_key]
        cutoff = now - window
        while events and events[0] < cutoff:
            events.popleft()

    def check_user_rate_limit(self, user_key: str, max_events: int, window: timedelta) -> bool:
        now = self._now()
        with self._lock:
            self._prune_user_events(user_key, now, window)
            return len(self._user_events[user_key]) < max_events

    def consume_user_rate_limit(self, user_key: str, window: timedelta) -> None:
        now = self._now()
        with self._lock:
            self._prune_user_events(user_key, now, window)
            self._user_events[user_key].append(now)

    def check_ai_quota(self, max_calls_per_day: int) -> bool:
        today = self._now().date()
        with self._lock:
            return self._ai_calls_by_day[today] < max_calls_per_day

    def consume_ai_quota(self) -> None:
        today = self._now().date()
        with self._lock:
            self._ai_calls_by_day[today] += 1

    def get_cached_evaluation(self, cache_key: str, ttl: timedelta) -> dict[str, Any] | None:
        now = self._now()
        with self._lock:
            cached = self._eval_cache.get(cache_key)
            if not cached:
                return None
            created_at, payload = cached
            if now - created_at > ttl:
                self._eval_cache.pop(cache_key, None)
                return None
            return payload

    def set_cached_evaluation(self, cache_key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._eval_cache[cache_key] = (self._now(), payload)


def build_cache_key(match_id: int, ball_number: int, field_input: str, bowler_input: str, strategy_input: str) -> str:
    normalized = "|".join(
        [
            str(match_id),
            str(ball_number),
            field_input.strip().lower(),
            bowler_input.strip().lower(),
            " ".join(strategy_input.strip().lower().split()),
        ]
    )
    return sha256(normalized.encode("utf-8")).hexdigest()


runtime_controls = RuntimeControls()
