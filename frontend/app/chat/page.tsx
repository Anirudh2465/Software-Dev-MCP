'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Cpu, User as UserIcon, Plus, Trash2, Sparkles, LogOut, Brain, Settings } from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const API_URL = 'http://localhost:8001';

export default function ChatPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();

    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [activeTab, setActiveTab] = useState("Work");
    const [chats, setChats] = useState<any[]>([]);
    const [currentChatId, setCurrentChatId] = useState<string | null>(null);
    const [persona, setPersona] = useState("Generalist");
    const [showPersonaMenu, setShowPersonaMenu] = useState(false);
    const [modes, setModes] = useState<any[]>([]);

    // --- Auth & Init ---
    useEffect(() => {
        if (!authLoading && !user) router.push('/login');
    }, [user, authLoading, router]);

    useEffect(() => {
        if (user) {
            const token = localStorage.getItem("token");
            if (!token) return router.push("/login");
            fetchModes();
            fetchChats(activeTab);
        }
    }, [activeTab, user, router]);

    useEffect(() => {
        // Immediate scroll on messge change
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }, [messages, loading]);

    // --- API Handlers ---
    const fetchModes = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/modes`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setModes(res.data.modes || []);
        } catch (err) { console.error(err); }
    };

    const fetchChats = async (mode: string) => {
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/chats?mode=${mode}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setChats(res.data);
            if (res.data.length > 0 && !currentChatId) {
                selectChat(res.data[0]._id);
            } else if (res.data.length === 0) {
                // Only create new chat if explicit user action or first load? 
                // Creating on every tab switch might be annoying if empty but ok.
                createNewChat(mode);
            }
        } catch (err) { console.error(err); }
    };

    const createNewChat = async (mode: string) => {
        try {
            const token = localStorage.getItem("token");
            const res = await axios.post(`${API_URL}/chats`, {
                title: `New ${mode} Chat`,
                mode: mode
            }, { headers: { Authorization: `Bearer ${token}` } });
            setChats(prev => [res.data, ...prev]);
            selectChat(res.data._id);
        } catch (err) { console.error(err); }
    };

    const selectChat = async (chatId: string) => {
        setCurrentChatId(chatId);
        try {
            const token = localStorage.getItem("token");
            const res = await axios.get(`${API_URL}/chats/${chatId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setMessages(res.data.messages || []);
        } catch (err) { console.error(err); }
    };

    const handleDeleteChat = async (e: React.MouseEvent, chatId: string) => {
        e.stopPropagation();
        if (!confirm("Delete this chat?")) return;
        try {
            const token = localStorage.getItem("token");
            await axios.delete(`${API_URL}/chats/${chatId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setChats(prev => prev.filter(c => c._id !== chatId));
            if (currentChatId === chatId) {
                setMessages([]);
                setCurrentChatId(null);
            }
        } catch (err) { console.error(err); }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !currentChatId) return;

        const userMsg = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const token = localStorage.getItem("token");
            const res = await axios.post(
                `${API_URL}/chat`,
                { message: userMsg.content, chat_id: currentChatId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with server." }]);
        } finally {
            setLoading(false);
        }
    };

    if (authLoading || !user) return <div className="h-screen w-full flex items-center justify-center bg-background text-foreground animate-pulse">Initializing...</div>;

    return (
        <div className="flex h-screen w-full bg-background text-foreground overflow-hidden font-sans selection:bg-accent selection:text-white pt-[73px]">
            <Navbar />

            {/* --- Sidebar --- */}
            <motion.aside
                initial={{ x: -30, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="w-72 bg-surface/50 border-r border-border backdrop-blur-xl flex flex-col z-20"
            >
                <div className="p-4 border-b border-border/50">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.5)]">
                                <Sparkles className="text-white w-5 h-5" />
                            </div>
                            <h1 className="text-xl font-bold tracking-tight">Jarvis</h1>
                        </div>

                        <div className="relative">
                            <button
                                onClick={() => setShowPersonaMenu(!showPersonaMenu)}
                                className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                title="Persona & Settings"
                            >
                                <Settings size={18} />
                            </button>

                            {showPersonaMenu && (
                                <div className="absolute top-full right-0 mt-2 w-48 bg-surface border border-white/10 rounded-xl shadow-2xl p-2 z-50 backdrop-blur-xl">
                                    <h3 className="text-[10px] uppercase font-bold text-gray-500 mb-2 px-2">System Persona</h3>
                                    {["Generalist", "Coder", "Architect", "Sentinel"].map(p => (
                                        <button
                                            key={p}
                                            onClick={async () => {
                                                setPersona(p);
                                                setShowPersonaMenu(false);
                                                try {
                                                    const token = localStorage.getItem("token");
                                                    await axios.post(`${API_URL}/persona`, { persona: p }, { headers: { Authorization: `Bearer ${token}` } });
                                                } catch (e) { console.error(e); }
                                            }}
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${persona === p ? 'bg-accent text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
                                        >
                                            {p}
                                        </button>
                                    ))}
                                    <div className="h-px bg-white/10 my-2" />
                                    <button
                                        onClick={() => router.push('/memory')}
                                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-pink-400 hover:bg-pink-500/10 transition-colors"
                                    >
                                        <Brain size={14} />
                                        <span>Memory Vault</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex bg-surface/80 rounded-lg p-1 gap-1 border border-border overflow-x-auto scrollbar-none">
                        {modes.map(mode => (
                            <button
                                key={mode.name}
                                onClick={() => {
                                    setActiveTab(mode.name);
                                    setMessages([]);
                                    setCurrentChatId(null);

                                    // Also tell backend to switch (optional but good for consistency)
                                    const token = localStorage.getItem("token");
                                    axios.post(`${API_URL}/mode`, { mode: mode.name }, { headers: { Authorization: `Bearer ${token}` } }).catch(console.error);
                                }}
                                className={`flex-1 min-w-[60px] py-1.5 text-xs font-medium rounded-md transition-all duration-300 whitespace-nowrap px-2 ${activeTab === mode.name
                                    ? "bg-accent text-white shadow-sm"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                                    }`}
                                title={mode.description || mode.name}
                            >
                                {mode.name}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin">
                    <button
                        onClick={() => createNewChat(activeTab)}
                        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-colors border border-dashed border-border/50 hover:border-accent/50 group"
                    >
                        <Plus className="w-4 h-4 text-gray-500 group-hover:text-accent transition-colors" />
                        <span>New Chat</span>
                    </button>

                    <div className="mt-4 space-y-1">
                        <h3 className="px-3 text-[10px] uppercase font-bold text-gray-600 tracking-wider mb-2">History</h3>
                        <AnimatePresence initial={false}>
                            {chats.map(chat => (
                                <motion.div
                                    key={chat._id}
                                    layout
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9, height: 0 }}
                                    transition={{ duration: 0.2 }}
                                    onClick={() => selectChat(chat._id)}
                                    className={`group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${currentChatId === chat._id
                                        ? "bg-white/5 text-white border border-white/5"
                                        : "text-gray-500 hover:text-gray-300 hover:bg-white/5 border border-transparent"
                                        }`}
                                >
                                    <div className="flex items-center gap-3 overflow-hidden">
                                        <span className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${currentChatId === chat._id ? 'bg-accent shadow-[0_0_8px_var(--accent)]' : 'bg-gray-700'}`} />
                                        <span className="truncate text-sm font-medium">{chat.title || "Untitled"}</span>
                                    </div>
                                    <button
                                        onClick={(e) => handleDeleteChat(e, chat._id)}
                                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>

                <div className="p-4 border-t border-border/50">
                    <div className="flex items-center gap-3 px-2 py-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-accent to-purple-600 flex items-center justify-center text-xs font-bold text-white">
                            {user?.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                            <p className="text-xs text-gray-500 truncate">Pro Plan</p>
                        </div>
                    </div>
                </div>
            </motion.aside>

            {/* --- Main Chat --- */}
            <main className="flex-1 flex flex-col relative bg-background/50">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-accent/10 via-transparent to-transparent pointer-events-none" />

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto px-4 md:px-20 py-6 scrollbar-thin scroll-smooth" ref={scrollRef}>
                    {messages.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="h-full flex flex-col items-center justify-center text-center space-y-6"
                        >
                            <div className="relative group cursor-default">
                                <div className="absolute -inset-1 bg-gradient-to-r from-accent to-purple-600 rounded-full blur opacity-25 group-hover:opacity-60 transition duration-1000 animate-pulse"></div>
                                <div className="relative w-24 h-24 rounded-2xl bg-surface/80 border border-white/10 flex items-center justify-center shadow-2xl backdrop-blur-sm">
                                    <Cpu className="w-10 h-10 text-accent drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]" />
                                </div>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                                    Good Evening, {user?.username}
                                </h2>
                                <p className="text-gray-500 max-w-md">I'm ready to help with your {activeTab.toLowerCase()} tasks. Initialize a request to begin.</p>
                            </div>
                        </motion.div>
                    ) : (
                        <div className="max-w-4xl mx-auto space-y-6 pb-10">
                            <AnimatePresence mode="popLayout">
                                {messages.map((msg, i) => (
                                    <motion.div
                                        key={i}
                                        layout="position"
                                        initial={{ opacity: 0, y: 40, scale: 0.98 }}
                                        whileInView={{ opacity: 1, y: 0, scale: 1 }}
                                        viewport={{ once: true, margin: "-50px" }}
                                        transition={{
                                            type: "spring",
                                            stiffness: 400,
                                            damping: 40,
                                            delay: 0.05
                                        }}
                                        className={`flex gap-5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                                    >
                                        <motion.div
                                            initial={{ scale: 0 }}
                                            whileInView={{ scale: 1 }}
                                            viewport={{ once: true }}
                                            className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 shadow-lg backdrop-blur-sm ${msg.role === 'user'
                                                ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-indigo-500/20'
                                                : 'bg-surface/60 border border-white/10'
                                                }`}
                                        >
                                            {msg.role === 'user' ? <UserIcon size={16} className="text-white" /> : <Cpu size={16} className="text-accent" />}
                                        </motion.div>

                                        <div className={`flex-1 overflow-hidden ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                                            <div className={`inline-block text-left relative max-w-[90%] ${msg.role === 'user'
                                                ? 'bg-gradient-to-br from-indigo-600/90 to-purple-700/90 border-t border-l border-white/10 text-white px-6 py-3.5 rounded-2xl rounded-tr-sm shadow-xl'
                                                : 'bg-surface/40 backdrop-blur-md border border-white/5 text-gray-200 px-6 py-4 rounded-2xl rounded-tl-sm'
                                                }`}>
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm, remarkMath]}
                                                    rehypePlugins={[rehypeKatex]}
                                                    components={{
                                                        p: ({ node, ...props }) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                                                        a: ({ node, ...props }) => <a className="text-accent hover:underline decoration-1 underline-offset-2" {...props} />,
                                                        code: ({ node, inline, className, children, ...props }: any) =>
                                                            !inline ? (
                                                                <div className="bg-[#0f0f0f]/80 border border-white/5 rounded-lg p-3 my-3 overflow-x-auto shadow-inner text-sm">
                                                                    <code className={className} {...props}>{children}</code>
                                                                </div>
                                                            ) : (
                                                                <code className="bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono text-accent-light" {...props}>{children}</code>
                                                            )
                                                    }}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>

                            {loading && (
                                <motion.div
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="flex gap-5"
                                >
                                    <div className="w-9 h-9 rounded-xl bg-surface/60 border border-white/10 flex items-center justify-center flex-shrink-0">
                                        <Cpu size={16} className="text-accent animate-pulse" />
                                    </div>
                                    <div className="flex items-center gap-1.5 h-9 px-2">
                                        <motion.span
                                            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut", delay: 0 }}
                                            className="w-1.5 h-1.5 bg-accent rounded-full"
                                        />
                                        <motion.span
                                            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut", delay: 0.2 }}
                                            className="w-1.5 h-1.5 bg-accent rounded-full"
                                        />
                                        <motion.span
                                            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut", delay: 0.4 }}
                                            className="w-1.5 h-1.5 bg-accent rounded-full"
                                        />
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-6">
                    <div className="max-w-4xl mx-auto relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-accent/50 to-purple-600/50 rounded-2xl blur opacity-20 group-hover:opacity-50 transition duration-500 will-change-transform"></div>
                        <form onSubmit={handleSubmit} className="relative bg-surface/80 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl flex items-center overflow-hidden transition-all focus-within:ring-1 focus-within:ring-accent/50 focus-within:bg-surface/90">
                            <div className="pl-4 pr-2">
                                <div className="p-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors text-gray-500 hover:text-white">
                                    <Plus size={20} />
                                </div>
                            </div>
                            <input
                                className="flex-1 bg-transparent border-none py-4 px-2 text-white placeholder-gray-500 focus:outline-none focus:ring-0 text-base"
                                placeholder="Type your message..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                autoFocus
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || loading}
                                className="mr-3 p-2 bg-white/5 hover:bg-accent text-white rounded-xl transition-all disabled:opacity-30 disabled:hover:bg-white/5 active:scale-95"
                            >
                                <Send size={18} />
                            </button>
                        </form>
                        <div className="text-center mt-3">
                            <p className="text-[10px] text-gray-600 uppercase tracking-widest font-medium group-hover:text-gray-500 transition-colors">Digital Synapse v2.0</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
