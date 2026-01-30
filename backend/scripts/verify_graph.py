import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.app.schemas.graph import GraphNode, GraphEdge, GraphData
from backend.app.services.graph_service import KnowledgeGraphService

def test_graph_service():
    print("Testing KnowledgeGraphService...")
    service = KnowledgeGraphService("data/test_graph.json")
    
    # Clear previous test
    service.clear_graph()
    
    # Add Node
    node1 = GraphNode(id="n1", label="Node 1", type="concept")
    service.add_node(node1)
    
    graph = service.get_graph()
    assert len(graph.nodes) == 1
    assert graph.nodes[0].id == "n1"
    print("Node addition verified.")
    
    # Add Edge
    node2 = GraphNode(id="n2", label="Node 2", type="concept")
    service.add_node(node2)
    edge = GraphEdge(id="e1", source="n1", target="n2", label="relates_to")
    service.add_edge(edge)
    
    graph = service.get_graph()
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    print("Edge addition verified.")
    
    # Clean up
    if os.path.exists("data/test_graph.json"):
        os.remove("data/test_graph.json")
    print("Cleanup done.")
    print("KnowledgeGraphService Test: PASSED")

if __name__ == "__main__":
    test_graph_service()
