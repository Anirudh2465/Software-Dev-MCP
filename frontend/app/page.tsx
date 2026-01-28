'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from './context/AuthContext';
import { Button, Input, Card } from '../components/ui/PremiumComponents';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Cpu, User as UserIcon, Sparkles, ArrowUp } from 'lucide-react';

const API_URL = 'http://localhost:8001';

export default function Home() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState("Work"); // Work or Personal
  const [chats, setChats] = useState<any[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Initial Data Fetch
  useEffect(() => {
    if (user) {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login");
        return;
      }
      fetchChats(activeTab);
    }
  }, [activeTab, user]); // Added user to dependencies

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
        // Create default if none exist? Or let user create.
        // automatically create one for convenience
        createNewChat(mode);
      }
    } catch (err) {
      console.error("Failed to fetch chats", err);
    }
  };

  const createNewChat = async (mode: string) => {
    try {
      const token = localStorage.getItem("token");
      const res = await axios.post(`${API_URL}/chats`, {
        title: `New ${mode} Chat`,
        mode: mode
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChats(prev => [res.data, ...prev]);
      selectChat(res.data._id);
    } catch (err) {
      console.error("Failed to create chat", err);
    }
  };

  const selectChat = async (chatId: string) => {
    setCurrentChatId(chatId);
    try {
      const token = localStorage.getItem("token");
      const res = await axios.get(`${API_URL}/chats/${chatId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error("Failed to fetch chat details", err);
    }
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
    } catch (err) {
      console.error("Failed to delete chat", err);
    }
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

      const assistantMsg = { role: 'assistant', content: res.data.response };
      setMessages(prev => [...prev, assistantMsg]);

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error communicating with server." }]);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) return <div className="h-screen w-full flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] container mx-auto px-4 gap-4">
      {/* Header Status */}
      <header className="flex justify-between items-center p-6 border-b border-white/10 backdrop-blur-md sticky top-0 z-10 bg-black/20">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Jarvis <span className="text-xs text-gray-500 font-mono">v2.0</span>
        </h1>
        <div className="flex gap-4">
          {/* Mode Toggles */}
          {["Work", "Personal"].map((mode) => (
            <button
              key={mode}
              onClick={() => {
                setActiveTab(mode);
                setMessages([]);
                setCurrentChatId(null);
              }} // Triggers fetch effect
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${activeTab === mode
                ? "bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                : "bg-white/5 text-gray-400 hover:bg-white/10"
                }`}
            >
              {mode}
            </button>
          ))}
          <button
            onClick={() => {
              localStorage.removeItem("token");
              router.push("/login");
            }}
            className="text-red-400 hover:text-red-300 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 border-r border-white/10 bg-black/20 p-4 overflow-y-auto hidden md:block">
          <button
            onClick={() => createNewChat(activeTab)}
            className="w-full py-2 mb-4 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>+</span> New Chat
          </button>
          <div className="space-y-2">
            {chats.map(chat => (
              <div
                key={chat._id}
                onClick={() => selectChat(chat._id)}
                className={`group p-3 rounded-lg cursor-pointer transition-all flex justify-between items-center ${currentChatId === chat._id ? 'bg-white/10 text-white' : 'hover:bg-white/5 text-gray-400'
                  }`}
              >
                <span className="truncate text-sm">{chat.title || "Untitled Chat"}</span>
                <button
                  onClick={(e) => handleDeleteChat(e, chat._id)}
                  className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 text-xs px-2"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full p-4">
          <div
            className="flex-1 overflow-y-auto space-y-6 p-4 scrollbar-hide"
            ref={scrollRef}
          >
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-500/20 to-purple-500/20 flex items-center justify-center backdrop-blur-xl border border-white/5">
                  <span className="text-2xl">✨</span>
                </div>
                <p>Select or create a chat to begin</p>
              </div>
            ) : (
              <AnimatePresence>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-indigo-600' : 'bg-blue-600'
                      }`}>
                      {msg.role === 'user' ? <UserIcon size={20} /> : <Cpu size={20} />}
                    </div>
                    <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user'
                      ? 'bg-indigo-600/20 border border-indigo-500/30 text-white rounded-tr-none'
                      : 'bg-white/10 border border-white/10 text-gray-100 rounded-tl-none'
                      }`}>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-4"
              >
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <Cpu size={20} />
                </div>
                <div className="bg-white/10 border border-white/10 rounded-2xl p-4 rounded-tl-none">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-0" />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-100" />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-white/10 bg-black/20 backdrop-blur-md sticky bottom-0">
            <div className="relative max-w-4xl mx-auto group">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Message Jarvis (${activeTab})...`}
                className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 pr-14
                            text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50
                            focus:bg-white/10 transition-all duration-300 shadow-lg"
                disabled={!currentChatId}
              />
              <button
                type="submit"
                disabled={loading || !input.trim() || !currentChatId}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-gradient-to-r from-blue-500 to-purple-600
                            rounded-xl text-white opacity-0 group-focus-within:opacity-100 disabled:opacity-50
                            transition-all duration-300 hover:scale-105 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
              >
                <ArrowUp size={20} />
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
