from __future__ import annotations

from typing import Mapping


def compose_runtime_env(env: Mapping[str, str]) -> dict[str, str]:
    """Return the compose environment used by LoopsBench tasks."""
    return dict(env)
