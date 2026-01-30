'use client';
import React, { useEffect, useState } from 'react';
import { Navbar } from '../../components/Navbar';
import GraphVisualizer from '../../components/GraphVisualizer';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

const API_URL = 'http://localhost:8001';

export default function GraphPage() {
    const { user } = useAuth();
    const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) fetchGraph();
    }, [user]);

    const fetchGraph = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/graph`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            console.log("Graph Data:", res.data);

            // Transform data for ReactFlow if needed
            // Assuming backend returns { nodes: [...], edges: [...] } matching ReactFlow structure roughly
            // We might need to map them if keys differ. Pydantic model vs ReactFlow Node:
            // Pydantic: id, label, type, position
            // ReactFlow: id, data: { label: ... }, position, type

            const nodes = res.data.nodes.map((n: any) => ({
                id: n.id,
                position: n.position || { x: Math.random() * 500, y: Math.random() * 500 },
                data: { label: n.label },
                type: 'default' // or n.type if valid
            }));

            const edges = res.data.edges.map((e: any) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.label,
                animated: true
            }));

            setGraphData({ nodes, edges });
        } catch (err) {
            console.error("Error fetching graph:", err);
        } finally {
            setLoading(false);
        }
    };

    const [inputText, setInputText] = useState("");
    const [generating, setGenerating] = useState(false);

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim()) return;
        setGenerating(true);
        try {
            const token = localStorage.getItem("token");
            await axios.post(`${API_URL}/graph/generate`, { text: inputText }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setInputText("");
            fetchGraph();
        } catch (err) {
            console.error(err);
            alert("Error generating graph");
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="h-screen w-full bg-background text-foreground overflow-hidden font-sans">
            <Navbar />
            <main className="pt-20 h-full w-full relative flex">
                {/* Sidebar Input */}
                <div className="w-80 bg-surface/50 border-r border-white/10 p-6 flex flex-col z-20 backdrop-blur-md">
                    <h2 className="text-xl font-bold text-white mb-4">Graph Builder</h2>
                    <p className="text-xs text-gray-400 mb-4">
                        Describe your project, ideas, or system architecture here. The AI will extract concepts and update the graph.
                    </p>
                    <form onSubmit={handleGenerate} className="flex-1 flex flex-col">
                        <textarea
                            className="flex-1 bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white resize-none focus:outline-none focus:border-accent"
                            placeholder="e.g. 'Project Alpha consists of a Frontend using React and a Backend using Python. It connects to a MongoDB database.'"
                            value={inputText}
                            onChange={e => setInputText(e.target.value)}
                        />
                        <button
                            disabled={generating || !inputText}
                            className="mt-4 py-3 bg-accent hover:bg-accent/80 text-white rounded-xl font-medium transition-all disabled:opacity-50"
                        >
                            {generating ? "Analyzing..." : "Update Graph"}
                        </button>
                    </form>
                </div>

                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex-1 bg-black/20 relative"
                >
                    {!loading && (
                        <GraphVisualizer
                            initialNodes={graphData.nodes}
                            initialEdges={graphData.edges}
                        />
                    )}
                </motion.div>
            </main>
        </div>
    );
}
