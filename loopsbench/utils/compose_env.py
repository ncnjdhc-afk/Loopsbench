from __future__ import annotations

from typing import Mapping


def with_legacy_lhb_aliases(env: Mapping[str, str]) -> dict[str, str]:
    """Mirror ``LOOPSBENCH_*`` compose vars to legacy ``LHB_*`` names.

    Old external tasks still interpolate ``${LHB_...}`` in ``docker-compose.yaml``.
    Compose resolves those placeholders on the host, so exporting both names keeps
    renamed harness code compatible without changing the task directories.
    """
    aliased = dict(env)
    for key, value in env.items():
        if key.startswith("LOOPSBENCH_"):
            aliased.setdefault("LHB_" + key.removeprefix("LOOPSBENCH_"), value)
    return aliased
