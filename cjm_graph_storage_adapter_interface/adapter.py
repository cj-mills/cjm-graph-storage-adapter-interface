"""The typed graph-storage task contract — the GraphStorageAdapter ABC + the GraphStorageToolProtocol (the first BORN-REAL tool protocol, stage-4 sqlite Option C migration).

Design notes (stage-4 ratified split): the BACKEND owns the translation — the
tool capability (sqlite-graph, future postgres-graph) owns connection/config/
lifecycle + schema + the per-backend translation of the typed query
expressions + the marked raw escape; what is generic across backends is
exactly this typed contract — one adapter, N backend tools (the transcription
matrix rotated: tools are backends instead of models). The protocol is BORN
REAL: stage 4 IS the sqlite plugin's Option C migration, so it derives from
the actual typed surface being built (contrast F6's fused-era mirrors that
re-derive at stage 8). The ADAPTER is the typed boundary: methods accept wire
dicts OR typed objects and normalize before touching the purely-typed tool;
results are wire-registered data nouns from cjm-context-graph-primitives
(retiring the last honest-dict graph results, C20/F8). Binding convention:
implementations are constructed with the bound tool instance —
AdapterClass(tool) — by the worker at task-channel bind time (CR-17 pt 2)."""

from abc import abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Protocol, runtime_checkable

from cjm_context_graph_primitives.graph import GraphContext, GraphEdge, GraphNode
from cjm_context_graph_primitives.provenance import SourceRef
from cjm_context_graph_primitives.query import (EdgeQuery, EdgeQueryResult, NodeQuery,
                                                NodeQueryResult, RawQuery, RawQueryResult)
from cjm_substrate.core.adapter import TaskAdapter


@runtime_checkable
class GraphStorageToolProtocol(Protocol):
    """Structural contract for graph-storage tool capabilities (BORN REAL —
    derived from the stage-4 typed surface, not a fused-era mirror).

    Each backend tool owns its per-backend translation of the typed query
    expressions and its raw escape (refusing `RawQuery.backend` mismatches).
    The surface is purely typed: graph nouns + query expressions in, typed
    results out.
    """

    # -- create (bulk; the queue path is the contract, D7)
    def add_nodes(self, nodes: List[GraphNode]) -> List[str]: ...
    def add_edges(self, edges: List[GraphEdge]) -> List[str]: ...

    # -- point reads + neighborhood + reverse provenance index
    def get_node(self, node_id: str) -> Optional[GraphNode]: ...
    def get_edge(self, edge_id: str) -> Optional[GraphEdge]: ...
    def get_context(self, node_id: str, depth: int = 1,
                    filter_labels: Optional[List[str]] = None) -> GraphContext: ...
    def find_nodes_by_source(self, source_ref: SourceRef) -> List[GraphNode]: ...
    def find_nodes_by_label(self, label: str, limit: int = 100) -> List[GraphNode]: ...

    # -- the typed query surface (stage 4; scale-shaped, portable)
    def query_nodes(self, query: NodeQuery) -> NodeQueryResult: ...
    def query_edges(self, query: EdgeQuery) -> EdgeQueryResult: ...
    def raw_query(self, query: RawQuery) -> RawQueryResult: ...

    # -- update / delete
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool: ...
    def update_edge(self, edge_id: str, properties: Dict[str, Any]) -> bool: ...
    def delete_nodes(self, node_ids: List[str], cascade: bool = True) -> int: ...
    def delete_edges(self, edge_ids: List[str]) -> int: ...

    # -- introspection / interchange
    def get_schema(self) -> Dict[str, Any]: ...
    def integrity_check(self) -> Dict[str, Any]: ...
    def import_graph(self, graph_data: GraphContext,
                     merge_strategy: str = "overwrite") -> Dict[str, int]: ...
    def export_graph(self, filter_query: Optional[NodeQuery] = None) -> GraphContext: ...


class GraphStorageAdapter(TaskAdapter):
    """The graph-storage task adapter — ONE multi-method, repository-style
    typed contract (pass-2 Thread 5 lock 1).

    Domain-neutral by lock 4: it stores generic `GraphNode`/`GraphEdge`;
    domain node construction (`Document`/`Segment`/`Correction`) stays in the
    consumer (or CR-18 sugar later). A domain-specific op such as
    `verify_spine` is deliberately OFF this surface — verification composes
    from the neutral query aggregates.

    Implementations run in-worker beside their tool capability and are
    constructed with the bound tool instance: `AdapterClass(tool)`. The
    adapter is the typed boundary — methods accept wire dicts or typed
    objects for DTO/expression arguments and normalize before touching the
    tool (whose protocol surface is purely typed).

    `integrity_check` is the typed introspection op institutionalizing the
    G3 corruption find: loop-backs assert storage health cheaply
    (sqlite -> `PRAGMA quick_check`).
    """

    task_name: ClassVar[str] = "graph-storage"
    required_tool_protocol: ClassVar[type] = GraphStorageToolProtocol

    def __init__(
        self,
        tool: GraphStorageToolProtocol,  # The bound tool capability instance (worker-side binding)
    ):
        self.tool = tool

    # -- create
    @abstractmethod
    def add_nodes(
        self,
        nodes: List[Any],  # GraphNodes or their wire dicts
    ) -> List[str]:  # Created node ids
        """Bulk-create nodes."""
        ...

    @abstractmethod
    def add_edges(
        self,
        edges: List[Any],  # GraphEdges or their wire dicts
    ) -> List[str]:  # Created edge ids
        """Bulk-create edges."""
        ...

    # -- point reads + neighborhood + reverse provenance index
    @abstractmethod
    def get_node(
        self,
        node_id: str,  # Node UUID
    ) -> Optional[GraphNode]:  # The node, or None
        """Fetch a single node by id."""
        ...

    @abstractmethod
    def get_edge(
        self,
        edge_id: str,  # Edge UUID
    ) -> Optional[GraphEdge]:  # The edge, or None
        """Fetch a single edge by id."""
        ...

    @abstractmethod
    def get_context(
        self,
        node_id: str,  # Center node UUID
        depth: int = 1,  # Traversal depth (whole-neighborhood reads; scale-shaped reads use query_*)
        filter_labels: Optional[List[str]] = None,  # Restrict returned nodes to these labels
    ) -> GraphContext:  # The neighborhood subgraph
        """Fetch a node's neighborhood subgraph."""
        ...

    @abstractmethod
    def find_nodes_by_source(
        self,
        source_ref: Any,  # SourceRef or its wire dict
    ) -> List[GraphNode]:  # Nodes whose sources match (content-hash-primary)
        """Reverse provenance lookup (content-hash-primary, CR-19)."""
        ...

    @abstractmethod
    def find_nodes_by_label(
        self,
        label: str,  # Node label
        limit: int = 100,  # Max nodes returned
    ) -> List[GraphNode]:  # Matching nodes
        """Fetch nodes by label."""
        ...

    # -- the typed query surface (stage 4)
    @abstractmethod
    def query_nodes(
        self,
        query: Any,  # NodeQuery or its tagged wire dict
    ) -> NodeQueryResult:  # Typed result (nodes / rows / count per query mode)
        """Execute a typed node query (server-side filter/order/page/count)."""
        ...

    @abstractmethod
    def query_edges(
        self,
        query: Any,  # EdgeQuery or its tagged wire dict
    ) -> EdgeQueryResult:  # Typed result (edges / rows / count per query mode)
        """Execute a typed edge query (server-side filter/order/page/count)."""
        ...

    @abstractmethod
    def raw_query(
        self,
        query: Any,  # RawQuery or its tagged wire dict (backend REQUIRED)
    ) -> RawQueryResult:  # Tabular backend-shaped result
        """Execute the marked, backend-coupled raw escape (the promotion forcing function)."""
        ...

    # -- update / delete
    @abstractmethod
    def update_node(
        self,
        node_id: str,  # Node UUID
        properties: Dict[str, Any],  # Properties to merge
    ) -> bool:  # True if the node existed
        """Merge properties into a node."""
        ...

    @abstractmethod
    def update_edge(
        self,
        edge_id: str,  # Edge UUID
        properties: Dict[str, Any],  # Properties to merge
    ) -> bool:  # True if the edge existed
        """Merge properties into an edge."""
        ...

    @abstractmethod
    def delete_nodes(
        self,
        node_ids: List[str],  # Node UUIDs
        cascade: bool = True,  # Also delete connected edges
    ) -> int:  # Number of nodes deleted
        """Bulk-delete nodes."""
        ...

    @abstractmethod
    def delete_edges(
        self,
        edge_ids: List[str],  # Edge UUIDs
    ) -> int:  # Number of edges deleted
        """Bulk-delete edges."""
        ...

    # -- introspection / interchange
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:  # Backend-reported schema/ontology summary
        """Report the stored graph's schema (labels, relation types, counts)."""
        ...

    @abstractmethod
    def integrity_check(self) -> Dict[str, Any]:  # {"ok": bool, "errors": List[str], "backend": str}
        """Backend self-check (G3 institutionalized; sqlite -> PRAGMA quick_check)."""
        ...

    @abstractmethod
    def import_graph(
        self,
        graph_data: Any,  # GraphContext or its wire dict
        merge_strategy: str = "overwrite",  # skip | overwrite | merge
    ) -> Dict[str, int]:  # Import counts per entity kind
        """Bulk-import a subgraph."""
        ...

    @abstractmethod
    def export_graph(
        self,
        filter_query: Optional[Any] = None,  # NodeQuery (or wire dict) selecting nodes; None = whole graph
    ) -> GraphContext:  # The exported subgraph (matching nodes + edges among them)
        """Export the graph (optionally filtered by a typed node query)."""
        ...
