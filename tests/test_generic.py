"""Contract-level test for GenericGraphStorageAdapter (projected from
nbs/generic.ipynb at the golden-reference flip): an in-memory fake tool
satisfying the protocol — the adapter is the typed boundary (wire dicts in,
typed objects to the tool, typed results out)."""

from typing import Dict, List

from cjm_context_graph_primitives.graph import GraphContext, GraphEdge, GraphNode
from cjm_context_graph_primitives.locators import FileRef
from cjm_context_graph_primitives.provenance import SourceRef
from cjm_context_graph_primitives.query import (EdgeQuery, EdgeQueryResult, NodeQuery,
                                                NodeQueryResult, RawQuery, RawQueryResult)
from cjm_context_graph_primitives.slices import CharSlice
from cjm_graph_storage_adapter_interface.adapter import GraphStorageToolProtocol
from cjm_graph_storage_adapter_interface.generic import GenericGraphStorageAdapter


class _FakeGraphTool:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.seen_types: List[type] = []  # records what the adapter handed us

    def add_nodes(self, nodes):
        self.seen_types.extend(type(n) for n in nodes)
        for n in nodes:
            self.nodes[n.id] = n
        return [n.id for n in nodes]

    def add_edges(self, edges):
        self.seen_types.extend(type(e) for e in edges)
        for e in edges:
            self.edges[e.id] = e
        return [e.id for e in edges]

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def get_edge(self, edge_id):
        return self.edges.get(edge_id)

    def get_context(self, node_id, depth=1, filter_labels=None):
        return GraphContext(nodes=list(self.nodes.values()), edges=list(self.edges.values()),
                            metadata={"center": node_id, "depth": depth})

    def find_nodes_by_source(self, source_ref):
        self.seen_types.append(type(source_ref))
        return [n for n in self.nodes.values()
                if any(s.content_hash == source_ref.content_hash for s in n.sources)]

    def find_nodes_by_label(self, label, limit=100):
        return [n for n in self.nodes.values() if n.label == label][:limit]

    def query_nodes(self, query):
        self.seen_types.append(type(query))
        ns = [n for n in self.nodes.values() if query.label is None or n.label == query.label]
        if query.count:
            return NodeQueryResult(count=len(ns))
        return NodeQueryResult(nodes=ns)

    def query_edges(self, query):
        self.seen_types.append(type(query))
        if query.count:
            return EdgeQueryResult(count=len(self.edges))
        return EdgeQueryResult(edges=list(self.edges.values()))

    def raw_query(self, query):
        self.seen_types.append(type(query))
        assert query.backend == "fake", "backend mismatch must be refused by real tools"
        return RawQueryResult(columns=["one"], rows=[[1]], row_count=1, backend="fake")

    def update_node(self, node_id, properties):
        n = self.nodes.get(node_id)
        if n is None:
            return False
        n.properties.update(properties)
        return True

    def update_edge(self, edge_id, properties):
        e = self.edges.get(edge_id)
        if e is None:
            return False
        e.properties.update(properties)
        return True

    def delete_nodes(self, node_ids, cascade=True):
        count = 0
        for nid in node_ids:
            if self.nodes.pop(nid, None) is not None:
                count += 1
                if cascade:
                    self.edges = {eid: e for eid, e in self.edges.items()
                                  if e.source_id != nid and e.target_id != nid}
        return count

    def delete_edges(self, edge_ids):
        return sum(1 for eid in edge_ids if self.edges.pop(eid, None) is not None)

    def get_schema(self):
        return {"labels": sorted({n.label for n in self.nodes.values()})}

    def integrity_check(self):
        return {"ok": True, "errors": [], "backend": "fake"}

    def import_graph(self, graph_data, merge_strategy="overwrite"):
        self.add_nodes(graph_data.nodes)
        self.add_edges(graph_data.edges)
        return {"nodes": len(graph_data.nodes), "edges": len(graph_data.edges)}

    def export_graph(self, filter_query=None):
        return GraphContext(nodes=list(self.nodes.values()), edges=list(self.edges.values()))


def test_generic_adapter_typed_boundary_contract():
    tool = _FakeGraphTool()
    assert isinstance(tool, GraphStorageToolProtocol)  # the structural contract holds

    adapter = GenericGraphStorageAdapter(tool)

    # wire dicts in -> the TOOL sees typed objects (the adapter is the typed boundary)
    node_dicts = [GraphNode(id="n1", label="Segment", properties={"index": 0, "text": "hi"}).to_dict(),
                  GraphNode(id="n2", label="Segment", properties={"index": 1, "text": ""}).to_dict()]
    ids = adapter.add_nodes(node_dicts)
    assert ids == ["n1", "n2"]
    edge_ids = adapter.add_edges([GraphEdge(id="e1", source_id="n1", target_id="n2",
                                            relation_type="NEXT").to_dict()])
    assert edge_ids == ["e1"]
    assert all(t in (GraphNode, GraphEdge) for t in tool.seen_types)

    # typed query via tagged wire dict -> typed result out
    res = adapter.query_nodes(NodeQuery(label="Segment", count=True).to_dict())
    assert isinstance(res, NodeQueryResult) and res.count == 2
    assert tool.seen_types[-1] is NodeQuery

    # typed objects pass through unchanged
    res2 = adapter.query_edges(EdgeQuery(count=True))
    assert isinstance(res2, EdgeQueryResult) and res2.count == 1

    # raw escape: typed dict normalization + backend marking flows through
    raw = adapter.raw_query(RawQuery(text="SELECT 1", backend="fake").to_dict())
    assert isinstance(raw, RawQueryResult) and raw.backend == "fake"

    # reverse index via wire dict


    ref = SourceRef(locator=FileRef(path="/runs/x.json"), content_hash="sha256:ab",
                    slice=CharSlice(0, 2))
    tool.nodes["n1"].sources.append(ref)
    hits = adapter.find_nodes_by_source(ref.to_dict())
    assert [n.id for n in hits] == ["n1"]

    # import/export round-trip through normalization
    exported = adapter.export_graph()
    tool2 = _FakeGraphTool()
    adapter2 = GenericGraphStorageAdapter(tool2)
    counts = adapter2.import_graph(exported.to_dict())
    assert counts == {"nodes": 2, "edges": 1}

    # introspection
    assert adapter.integrity_check()["ok"] is True
    assert adapter.get_schema() == {"labels": ["Segment"]}

    # update/delete forwarding
    assert adapter.update_node("n1", {"text": "edited"}) is True
    assert adapter.delete_edges(["e1"]) == 1
    assert adapter.delete_nodes(["n1", "n2"]) == 2
