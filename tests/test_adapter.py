"""Contract-level checks for the graph-storage task contract (projected from
nbs/adapter.ipynb at the golden-reference flip): the ABC is abstract, the
ClassVars are set, and the protocol is runtime-checkable for structural
isinstance."""

import pytest

from cjm_graph_storage_adapter_interface.adapter import (GraphStorageAdapter,
                                                         GraphStorageToolProtocol)


class _NotAGraphTool:
    def add_nodes(self, nodes): ...


def test_abstract_gate_refuses_instantiation():
    with pytest.raises(TypeError):
        GraphStorageAdapter(tool=None)  # type: ignore[abstract]


def test_classvars_and_protocol_identity():
    assert GraphStorageAdapter.task_name == "graph-storage"
    assert GraphStorageAdapter.required_tool_protocol is GraphStorageToolProtocol


def test_partial_surface_fails_structural_check():
    assert not isinstance(_NotAGraphTool(), GraphStorageToolProtocol)
