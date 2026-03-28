"""Utility functions for OpenConch."""

import uuid
import time
from typing import Optional


def generate_id() -> str:
    """Generate a unique memory ID."""
    return str(uuid.uuid4())


def now_timestamp() -> float:
    """Current time as Unix timestamp."""
    return time.time()


def cosine_similarity(a, b) -> float:
    """Compute cosine similarity between two vectors."""
    import numpy as np
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)
