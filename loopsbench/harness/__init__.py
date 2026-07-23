from __future__ import annotations

from loopsbench.harness.instruction_composer import compose_instruction

__all__ = ["Harness", "compose_instruction"]


def __getattr__(name: str):
    if name == "Harness":
        from loopsbench.harness.harness import Harness

        return Harness
    raise AttributeError(name)
