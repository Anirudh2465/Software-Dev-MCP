'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button, Card } from '../../components/ui/PremiumComponents';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, FileText, Activity } from 'lucide-react';

const API_URL = 'http://localhost:8001';

export default function MemoryPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [modes, setModes] = useState<string[]>([]);
    const [selectedMode, setSelectedMode] = useState("Work");
    const [memories, setMemories] = useState<{ semantic: any[], episodic: any[] }>({ semantic: [], episodic: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        }
    }, [user, authLoading, router]);

    useEffect(() => {
        if (user) {
            fetchModes();
        }
    }, [user]);

    useEffect(() => {
        if (user && selectedMode) {
            fetchMemories();
        }
    }, [user, selectedMode]);

    const fetchModes = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API_URL}/modes`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setModes(res.data.modes);
            if (res.data.current_mode) setSelectedMode(res.data.current_mode);
        } catch (err) {
            console.error("Failed to fetch modes", err);
        }
    };

    const fetchMemories = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`${API_URL}/memory/${selectedMode}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setMemories(res.data);
        } catch (err) {
            console.error("Failed to fetch memories", err);
        } finally {
            setLoading(false);
        }
    };

    const deleteFact = async (id: string) => {
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API_URL}/memory/semantic/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchMemories();
        } catch (err) {
            console.error("Failed to delete fact", err);
        }
    };

    const deleteEpisode = async (id: string) => {
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API_URL}/memory/episodic/${id}?mode=${selectedMode}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchMemories();
        } catch (err) {
            console.error("Failed to delete episode", err);
        }
    };

    if (authLoading || !user) return null;

    return (
        <div className="container mx-auto px-4 py-8">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col gap-8"
            >
                <div className="flex flex-col md:flex-row justify-between items-center bg-white/5 p-6 rounded-2xl backdrop-blur-md border border-white/10">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Memory Bank</h1>
                        <p className="text-gray-400 mt-1">Manage what Jarvis knows about you in {selectedMode} mode</p>
                    </div>
                    <div className="flex gap-2 mt-4 md:mt-0 overflow-x-auto pb-2 md:pb-0">
                        {modes.map(mode => (
                            <button
                                key={mode}
                                onClick={() => setSelectedMode(mode)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${selectedMode === mode
                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                                    }`}
                            >
                                {mode}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Semantic Memory Column */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="text-blue-400" />
                            <h2 className="text-xl font-semibold text-white">Core Facts</h2>
                        </div>
                        {loading ? (
                            <div className="text-center text-gray-500 py-10">Loading facts...</div>
                        ) : memories.semantic.length === 0 ? (
                            <div className="text-center text-gray-600 py-10 bg-white/5 rounded-xl border border-white/5 border-dashed">No facts stored</div>
                        ) : (
                            <AnimatePresence>
                                {memories.semantic.map((item: any) => (
                                    <motion.div
                                        key={item.id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                    >
                                        <Card className="!p-4 bg-white/5 hover:bg-white/10 transition-colors group relative border-l-4 border-l-blue-500">
                                            <p className="text-gray-200 pr-8">{item.fact}</p>
                                            <span className="text-xs text-gray-500 mt-2 block">{new Date(item.timestamp).toLocaleString()}</span>
                                            <button
                                                onClick={() => deleteFact(item.id)}
                                                className="absolute top-4 right-4 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </Card>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        )}
                    </div>

                    {/* Episodic Memory Column */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-4">
                            <Activity className="text-purple-400" />
                            <h2 className="text-xl font-semibold text-white">Experiences</h2>
                        </div>
                        {loading ? (
                            <div className="text-center text-gray-500 py-10">Loading episodes...</div>
                        ) : memories.episodic.length === 0 ? (
                            <div className="text-center text-gray-600 py-10 bg-white/5 rounded-xl border border-white/5 border-dashed">No episodes stored</div>
                        ) : (
                            <AnimatePresence>
                                {memories.episodic.map((item: any) => (
                                    <motion.div
                                        key={item.id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                    >
                                        <Card className="!p-4 bg-white/5 hover:bg-white/10 transition-colors group relative border-l-4 border-l-purple-500">
                                            <p className="text-gray-200 pr-8 text-sm">{item.content}</p>
                                            <span className="text-xs text-gray-500 mt-2 block">
                                                {item.metadata?.timestamp ? new Date(item.metadata.timestamp).toLocaleString() : 'Unknown Time'}
                                            </span>
                                            <button
                                                onClick={() => deleteEpisode(item.id)}
                                                className="absolute top-4 right-4 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </Card>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
