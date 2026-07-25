from __future__ import annotations

from types import SimpleNamespace

from loopsbench.agents.agent_factory import AgentFactory
from loopsbench.agents.agent_name import AgentName
from loopsbench.agents.base_agent import BaseAgent


class _FakeOracleAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "oracle"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = kwargs

    def perform_task(self, *args, **kwargs):
        raise NotImplementedError


def test_agent_factory_lazy_imports_requested_agent_only(monkeypatch) -> None:
    imported_modules: list[str] = []

    def _fake_import_module(module_path: str):
        imported_modules.append(module_path)
        if module_path != "loopsbench.agents.oracle_agent":
            raise AssertionError(f"unexpected import: {module_path}")
        return SimpleNamespace(OracleAgent=_FakeOracleAgent)

    monkeypatch.setattr(
        "loopsbench.agents.agent_factory.importlib.import_module", _fake_import_module
    )

    agent_cls = AgentFactory.get_agent_class(agent_name=AgentName.ORACLE)

    assert agent_cls is _FakeOracleAgent
    assert imported_modules == ["loopsbench.agents.oracle_agent"]


def test_agent_factory_get_agent_instantiates_loaded_class(monkeypatch) -> None:
    monkeypatch.setattr(
        AgentFactory,
        "_load_built_in_agent_class",
        classmethod(lambda cls, agent_name: _FakeOracleAgent),
    )

    agent = AgentFactory.get_agent(agent_name=AgentName.ORACLE, dataset_path="tasks")

    assert isinstance(agent, _FakeOracleAgent)
    assert agent.kwargs == {"dataset_path": "tasks"}
