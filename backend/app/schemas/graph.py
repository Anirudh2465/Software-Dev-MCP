from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "default"  # concept, entity, etc.
    data: Dict[str, Any] = {}
    position: Dict[str, float] = {"x": 0, "y": 0}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: str = "default"

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class GraphUpdate(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    action: str = "merge"  # merge, replace
