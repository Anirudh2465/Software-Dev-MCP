
'use client';
import React, { useState, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { Button, Input, Card } from '../../components/ui/PremiumComponents';
import { Folder, RefreshCw, Trash2, Plus, FileText, Monitor } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

// Hardcoded for now if not in context, but using same assumption as other pages
const API_URL = 'http://localhost:8001'; // Default fastapi port, checked in metadata

export default function FilesPage() {
    const { user } = useAuth();
    const [token, setToken] = useState<string | null>(null);
    const [directories, setDirectories] = useState<any[]>([]);
    const [newPath, setNewPath] = useState("");
    const [loading, setLoading] = useState(false);
    const [selectedDir, setSelectedDir] = useState<any>(null);
    const [files, setFiles] = useState<any[]>([]);

    useEffect(() => {
        // Safe access to localStorage
        const t = localStorage.getItem('token');
        setToken(t);
    }, []);

    useEffect(() => {
        if (token) fetchDirectories();
    }, [token]);

    const fetchDirectories = async () => {
        try {
            const res = await fetch(`${API_URL}/files/monitored`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDirectories(data);
            }
        } catch (e) {
            console.error("Error fetching directories", e);
        }
    };

    const browseDirectory = async () => {
        try {
            const res = await fetch(`${API_URL}/files/browse`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.path) {
                    setNewPath(data.path);
                }
            }
        } catch (e) {
            console.error("Error browsing", e);
        }
    };

    const addDirectory = async () => {
        if (!newPath) return;
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/files/monitored`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ path: newPath })
            });
            if (res.ok) {
                setNewPath("");
                fetchDirectories();
            } else {
                const err = await res.json();
                alert(err.detail);
            }
        } catch (e) {
            alert("Error adding directory");
        }
        setLoading(false);
    };

    const removeDirectory = async (path: string) => {
        try {
            const res = await fetch(`${API_URL}/files/monitored?path=${encodeURIComponent(path)}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) fetchDirectories();
        } catch (e) {
            console.error(e);
        }
    };

    const scanDirectory = async (path: string) => {
        try {
            await fetch(`${API_URL}/files/scan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ path })
            });
        } catch (e) {
            console.error(e);
        }
    };

    const [currentPath, setCurrentPath] = useState<string>("");

    const viewFiles = async (targetPath: string) => {
        const dir = directories.find(d => d.path === targetPath);
        if (dir) setSelectedDir(dir);

        setCurrentPath(targetPath);
        setFiles([]);
        try {
            const res = await fetch(`${API_URL}/files/list?path=${encodeURIComponent(targetPath)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setFiles(data.items || []);
            } else {
                setFiles([]);
            }
        } catch (e) {
            setFiles([]);
        }
    };

    const navigateUp = () => {
        if (!currentPath) return;
        let parent = "";
        if (currentPath.includes("\\")) {
            parent = currentPath.substring(0, currentPath.lastIndexOf("\\"));
            if (parent.endsWith(":")) parent += "\\";
        } else {
            parent = currentPath.substring(0, currentPath.lastIndexOf("/"));
        }
        if (parent && parent !== currentPath) {
            viewFiles(parent);
        }
    };

    return (
        <div className="min-h-screen bg-transparent text-foreground font-sans">
            <Navbar />

            <main className="pt-24 px-6 max-w-6xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <header className="mb-10 text-center">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-4 backdrop-blur-md">
                            <Monitor size={14} className="text-blue-400" />
                            <span className="text-xs font-medium text-gray-300">System Access</span>
                        </div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-300 to-indigo-300 bg-clip-text text-transparent mb-2">
                            Monitored Directories
                        </h1>
                        <p className="text-gray-400">Manage local file system access for the Agent.</p>
                    </header>

                    {/* Add New */}
                    <Card className="mb-8 !py-4 flex gap-4 items-center">
                        <div className="flex-1 flex gap-2">
                            <Button onClick={browseDirectory} className="!py-3 !px-4 !bg-white/10 hover:!bg-white/20 !text-gray-200" title="Browse Folder">
                                <Folder size={18} />
                            </Button>
                            <Input
                                value={newPath}
                                onChange={(e: any) => setNewPath(e.target.value)}
                                placeholder="Enter absolute path (e.g. D:\Projects\MyApp)"
                            />
                        </div>
                        <Button onClick={addDirectory} disabled={loading} className="!py-3">
                            {loading ? <RefreshCw className="animate-spin" /> : <Plus />} Add Path
                        </Button>
                    </Card>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Directory List */}
                        <div className="space-y-4">
                            <h2 className="text-xl font-semibold text-white/80 mb-4 flex items-center gap-2">
                                <Folder className="text-yellow-500" /> Directories
                            </h2>
                            {directories.map((dir, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.1 }}
                                    className={`p-4 rounded-xl border transition-all cursor-pointer hover:bg-white/5 ${selectedDir?.path === dir.path ? 'bg-white/10 border-blue-500' : 'bg-surface/30 border-white/5'}`}
                                    onClick={() => viewFiles(dir.path)}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="overflow-hidden">
                                            <p className="font-mono text-sm text-blue-200 truncate" title={dir.path}>{dir.path}</p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                Last Scanned: {dir.last_scanned ? new Date(dir.last_scanned).toLocaleString() : 'Never'}
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button onClick={(e) => { e.stopPropagation(); scanDirectory(dir.path); }} className="p-2 hover:bg-blue-500/20 rounded-lg text-blue-400 transition-colors" title="Scan Now">
                                                <RefreshCw size={16} />
                                            </button>
                                            <button onClick={(e) => { e.stopPropagation(); removeDirectory(dir.path); }} className="p-2 hover:bg-red-500/20 rounded-lg text-red-400 transition-colors" title="Remove">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                            {directories.length === 0 && (
                                <p className="text-gray-500 italic">No monitored directories.</p>
                            )}
                        </div>

                        {/* File Browser */}
                        <div className="bg-black/20 rounded-2xl border border-white/5 p-6 h-[500px] overflow-hidden flex flex-col">
                            <h2 className="text-xl font-semibold text-white/80 mb-4 flex items-center gap-2">
                                <FileText className="text-cyan-500" />
                                File Explorer
                            </h2>

                            {currentPath && (
                                <div className="mb-4">
                                    <div className="text-xs font-mono text-gray-400 mb-2 border-b border-white/5 pb-2 break-all">
                                        {currentPath}
                                    </div>
                                    <Button onClick={navigateUp} className="!py-1 !px-3 !text-xs !bg-white/10 hover:!bg-white/20">
                                        .. Parent Directory
                                    </Button>
                                </div>
                            )}

                            <div className="flex-1 overflow-y-auto space-y-1 pr-2 scrollbar-thin scrollbar-thumb-white/10">
                                {files.length > 0 ? (
                                    files.map((f, i) => (
                                        <div
                                            key={i}
                                            className="flex justify-between items-center p-2 hover:bg-white/5 rounded text-sm group cursor-pointer transition-colors"
                                            onClick={() => f.type === 'directory' ? viewFiles(f.path) : null}
                                        >
                                            <div className="flex items-center gap-2 overflow-hidden">
                                                {f.type === 'directory' ? (
                                                    <Folder size={16} className="text-yellow-500 flex-shrink-0" />
                                                ) : (
                                                    <FileText size={16} className="text-blue-400 flex-shrink-0" />
                                                )}
                                                <span className={`truncate ${f.type === 'directory' ? 'text-yellow-100 font-medium' : 'text-gray-300'}`}>
                                                    {f.name}
                                                </span>
                                            </div>
                                            <span className="text-xs text-gray-600 group-hover:text-gray-400 flex-shrink-0 ml-2">
                                                {f.type === 'file' ? (f.size / 1024).toFixed(1) + ' KB' : ''}
                                            </span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-2">
                                        <Folder size={48} className="opacity-20" />
                                        <p>{currentPath ? "Empty Directory" : "Select a root directory to browse"}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </motion.div>
            </main>
        </div>
    );
}
