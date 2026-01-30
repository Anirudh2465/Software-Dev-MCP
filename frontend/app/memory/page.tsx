'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Trash2, Database, Brain, Sparkles, Layers, Search } from 'lucide-react';
import { Navbar } from '../../components/Navbar';

const API_URL = 'http://localhost:8001';

export default function MemoryPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();

    const [activeMode, setActiveMode] = useState("Work");
    const [activeTab, setActiveTab] = useState<"semantic" | "episodic">("semantic");
    const [data, setData] = useState<{ semantic: any[], episodic: any[] }>({ semantic: [], episodic: [] });
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");
    const [modes, setModes] = useState<any[]>([]);

    useEffect(() => {
        if (!authLoading && !user) router.push('/login');
        if (user) fetchModes();
    }, [user, authLoading, router]);

    useEffect(() => {
        if (user) fetchMemory(activeMode);
    }, [user, activeMode]);

    const fetchModes = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/modes`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setModes(res.data.modes || []);
        } catch (err) { console.error(err); }
    };

    const fetchMemory = async (mode: string) => {
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/memory/${mode}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setData(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const deleteFact = async (id: string) => {
        if (!confirm("Delete this fact? It will also remove related conversation history.")) return;
        try {
            const token = localStorage.getItem("token");
            await axios.delete(`${API_URL}/memory/semantic/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setData(prev => ({ ...prev, semantic: prev.semantic.filter(i => i._id !== id) }));
        } catch (err) { console.error(err); }
    };

    const deleteEpisode = async (id: string) => {
        if (!confirm("Delete this memory episode?")) return;
        try {
            const token = localStorage.getItem("token");
            await axios.delete(`${API_URL}/memory/episodic/${id}?mode=${activeMode}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setData(prev => ({ ...prev, episodic: prev.episodic.filter(i => i.id !== id) }));
        } catch (err) { console.error(err); }
    };

    const filteredData = (activeTab === "semantic" ? data.semantic : data.episodic).filter(item => {
        const content = activeTab === "semantic" ? item.fact : item.content;
        return content?.toLowerCase().includes(search.toLowerCase());
    });

    return (
        <div className="flex flex-col h-screen w-full bg-background/50 text-foreground overflow-hidden font-sans pt-[73px]">
            <Navbar />

            {/* Sub-Header */}
            <header className="h-14 border-b border-border/50 bg-surface/30 backdrop-blur-md flex items-center justify-between px-6 z-10 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-pink-600 flex items-center justify-center shadow-[0_0_15px_rgba(219,39,119,0.5)]">
                            <Brain className="text-white w-5 h-5" />
                        </div>
                        <h1 className="text-xl font-bold tracking-tight">Memory Vault</h1>
                    </div>
                </div>

                <div className="flex items-center gap-2 bg-surface/80 rounded-lg p-1 border border-border overflow-x-auto scrollbar-none">
                    {modes.map(mode => (
                        <button
                            key={mode.name}
                            onClick={() => setActiveMode(mode.name)}
                            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap ${activeMode === mode.name
                                ? "bg-white/10 text-white shadow-sm"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                }`}
                            title={mode.description}
                        >
                            {mode.name}
                        </button>
                    ))}
                </div>
            </header>

            {/* Content */}
            <main className="flex-1 overflow-hidden flex flex-col p-6 md:p-10 relative">
                <div className="max-w-6xl w-full mx-auto flex-1 flex flex-col gap-6">

                    {/* Controls */}
                    <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
                        <div className="flex gap-4">
                            <TabButton active={activeTab === "semantic"} onClick={() => setActiveTab("semantic")} icon={Database} label="Core Facts" />
                            <TabButton active={activeTab === "episodic"} onClick={() => setActiveTab("episodic")} icon={Layers} label="Episodic History" />
                        </div>

                        <div className="relative w-full md:w-64 group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-accent transition-colors" />
                            <input
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Search memories..."
                                className="w-full bg-surface/50 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all"
                            />
                        </div>
                    </div>

                    {/* Grid */}
                    <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin">
                        {loading ? (
                            <div className="flex justify-center items-center h-40">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                            </div>
                        ) : filteredData.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 text-gray-500 gap-4">
                                <Sparkles className="w-12 h-12 opacity-20" />
                                <p>No {activeTab === "semantic" ? "facts" : "episodes"} found for {activeMode} mode.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <AnimatePresence>
                                    {filteredData.map((item, i) => (
                                        <motion.div
                                            key={item._id || item.id || i}
                                            layout
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            transition={{ duration: 0.2, delay: i * 0.05 }}
                                            className="bg-surface/40 backdrop-blur-md border border-white/5 p-5 rounded-2xl hover:border-white/10 hover:bg-surface/60 transition-all group relative overflow-hidden"
                                        >
                                            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => activeTab === "semantic" ? deleteFact(item._id) : deleteEpisode(item.id)}
                                                    className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>

                                            <div className="flex items-start gap-3 mb-3">
                                                <div className={`p-2 rounded-lg ${activeTab === "semantic" ? "bg-amber-500/10 text-amber-500" : "bg-blue-500/10 text-blue-500"}`}>
                                                    {activeTab === "semantic" ? <Database size={16} /> : <Layers size={16} />}
                                                </div>
                                                <div className="text-xs font-mono text-gray-500 mt-1">
                                                    {activeTab === "semantic" ? "FACT" : "EPISODE"}
                                                </div>
                                            </div>

                                            <p className="text-sm text-gray-200 leading-relaxed">
                                                {activeTab === "semantic" ? item.fact : item.content}
                                            </p>

                                            <div className="mt-4 text-[10px] text-gray-600 font-mono">
                                                ID: {(item._id || item.id)?.substring(0, 8)}...
                                            </div>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

function TabButton({ active, onClick, icon: Icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${active
                ? "bg-white/10 text-white shadow-lg border border-white/10"
                : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
        >
            <Icon size={16} />
            <span>{label}</span>
        </button>
    );
}
