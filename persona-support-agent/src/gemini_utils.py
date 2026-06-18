from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def is_gemini_quota_error(exc: Exception) -> bool:
    message = str(exc)
    return "RESOURCE_EXHAUSTED" in message or "429" in message


def call_gemini_with_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = 5,
    **kwargs,
) -> T:
    """Retry Gemini calls with exponential backoff for transient rate limits."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if is_gemini_quota_error(exc) or attempt == max_retries - 1:
                raise exc
            sleep_time = (2**attempt) + random.uniform(0, 1)
            time.sleep(sleep_time)
    raise RuntimeError("Gemini call failed after retries")
