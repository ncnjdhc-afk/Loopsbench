from __future__ import annotations

__all__ = ["Harness"]


def __getattr__(name: str):
    if name == "Harness":
        from loopsbench.harness.harness import Harness

        return Harness
    raise AttributeError(name)
