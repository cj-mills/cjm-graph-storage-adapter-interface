# cjm-graph-storage-adapter-interface

<!-- generated from the context graph by `cjm-context-graph readme` — do not edit by hand; edit the graph (the urge to hand-edit = move it on-graph) -->

_No purpose recorded on-graph yet — author it with_ `assert e8507dbf-926d-5169-8be2-0ddcc775fead purpose "…"` _(or by the repo's entity key)._

## Modules

- **`cjm_graph_storage_adapter_interface.__init__`**
- **`cjm_graph_storage_adapter_interface.adapter`** — The typed graph-storage task contract — the GraphStorageAdapter ABC + the GraphStorageToolProtocol (the first BORN-REAL tool protocol, stage-4 sqlite Option C migration).
- **`cjm_graph_storage_adapter_interface.generic`** — GenericGraphStorageAdapter — the backend-agnostic graph-storage task implementation: wire-input normalization + forwarding (wire dicts or typed objects in, purely-typed tool arguments, typed results through).

## API

### `cjm_graph_storage_adapter_interface.adapter`

- `GraphStorageAdapter` _class_ — The graph-storage task adapter — ONE multi-method, repository-style
- `GraphStorageToolProtocol` _class_ — Structural contract for graph-storage tool capabilities (BORN REAL —

### `cjm_graph_storage_adapter_interface.generic`

- `GenericGraphStorageAdapter` _class_ — Generic graph-storage adapter: normalize wire inputs, forward to the
- `ensure_context` _function_ — Normalize a wire dict to a `GraphContext` (typed values pass through).
- `ensure_edge` _function_ — Normalize a wire dict to a `GraphEdge` (typed values pass through).
- `ensure_edge_query` _function_ — Normalize a tagged wire dict to an `EdgeQuery` (typed values pass through).
- `ensure_node` _function_ — Normalize a wire dict to a `GraphNode` (typed values pass through).
- `ensure_node_query` _function_ — Normalize a tagged wire dict to a `NodeQuery` (typed values pass through).
- `ensure_query` _function_ — Normalize either typed query by its wire tag (`edge_query` is an edge query, anything
- `ensure_raw_query` _function_ — Normalize a tagged wire dict to a `RawQuery` (typed values pass through).
- `ensure_source_ref` _function_ — Normalize a wire dict to a `SourceRef` (typed values pass through).

## Dependencies

**Depends on:** `cjm-context-graph-primitives`, `cjm-substrate`
