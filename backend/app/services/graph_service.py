import json
import os
from pathlib import Path
from typing import List, Dict, Any
from ..schemas.graph import GraphData, GraphNode, GraphEdge

class KnowledgeGraphService:
    def __init__(self, storage_path: str = "data/knowledge_graph.json"):
        self.storage_path = Path(os.getcwd()) / storage_path
        self.ensure_storage()
        self.graph = self.load_graph()

    def ensure_storage(self):
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.save_graph(GraphData(nodes=[], edges=[]))

    def load_graph(self) -> GraphData:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                return GraphData(**data)
        except Exception as e:
            print(f"Error loading graph: {e}")
            return GraphData(nodes=[], edges=[])

    def save_graph(self, graph: GraphData):
        with open(self.storage_path, "w") as f:
            f.write(graph.model_dump_json(indent=2))

    def get_graph(self) -> GraphData:
        return self.graph

    def add_node(self, node: GraphNode):
        # Check if node exists
        if not any(n.id == node.id for n in self.graph.nodes):
            self.graph.nodes.append(node)
            self.save_graph(self.graph)

    def add_edge(self, edge: GraphEdge):
         # Check if edge exists
        if not any(e.id == edge.id for e in self.graph.edges):
            self.graph.edges.append(edge)
            self.save_graph(self.graph)

    def update_graph(self, update_data: GraphData):
        """Merges new nodes and edges into existing graph"""
        existing_node_ids = {n.id for n in self.graph.nodes}
        existing_edge_ids = {e.id for e in self.graph.edges}

        for node in update_data.nodes:
            if node.id not in existing_node_ids:
                self.graph.nodes.append(node)
                existing_node_ids.add(node.id)
            else:
                # Update existing node data/position if needed?
                pass 

        for edge in update_data.edges:
            if edge.id not in existing_edge_ids:
                self.graph.edges.append(edge)
                existing_edge_ids.add(edge.id)

        self.save_graph(self.graph)
        return self.graph

    def clear_graph(self):
        self.graph = GraphData(nodes=[], edges=[])
        self.save_graph(self.graph)
