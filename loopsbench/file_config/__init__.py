"""Filesystem-backed LoopsBench run and model-runtime configuration."""

from __future__ import annotations

__all__ = [
    "LoopsBenchModelRuntimeFileConfig",
    "LoopsBenchRunFileConfig",
    "apply_model_runtime_config",
    "load_model_runtime_file",
    "load_run_file",
    "merge_agent_kwargs",
    "resolve_run_params",
]


def __getattr__(name: str):
    if name in {
        "apply_model_runtime_config",
        "load_model_runtime_file",
        "load_run_file",
        "merge_agent_kwargs",
    }:
        from loopsbench.file_config import io

        return getattr(io, name)
    if name == "LoopsBenchModelRuntimeFileConfig":
        from loopsbench.file_config.model_runtime_file import (
            LoopsBenchModelRuntimeFileConfig,
        )

        return LoopsBenchModelRuntimeFileConfig
    if name == "LoopsBenchRunFileConfig":
        from loopsbench.file_config.run_file import LoopsBenchRunFileConfig

        return LoopsBenchRunFileConfig
    if name == "resolve_run_params":
        from loopsbench.file_config.resolve import resolve_run_params

        return resolve_run_params
    raise AttributeError(name)
