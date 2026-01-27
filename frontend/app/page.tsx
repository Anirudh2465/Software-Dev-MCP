"use client";
import { useState, useEffect, useRef } from "react";
import { Send, User, Bot, Briefcase, Coffee, Loader2, Plus, Trash2, Database, X } from "lucide-react";

interface Message {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("Work");
  const [availableModes, setAvailableModes] = useState<string[]>(["Work", "Personal"]);
  const [showMemory, setShowMemory] = useState(false);
  const [memoryFacts, setMemoryFacts] = useState<string[]>([]);
  const [newModeName, setNewModeName] = useState("");
  const [showAddMode, setShowAddMode] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchModes();
  }, []);

  // Refresh memory when mode changes or memory view is opened
  useEffect(() => {
    if (showMemory) {
      fetchMemory();
    }
  }, [showMemory, mode]);

  const fetchModes = async () => {
    try {
      const res = await fetch("http://localhost:8001/modes");
      const data = await res.json();
      setAvailableModes(data.modes);
      setMode(data.current_mode);
    } catch (e) {
      console.error("Failed to fetch modes", e);
    }
  };

  const fetchMemory = async () => {
    try {
      const res = await fetch(`http://localhost:8001/memory/${mode}`);
      const data = await res.json();
      setMemoryFacts(data.facts);
    } catch (e) {
      console.error("Failed to fetch memory", e);
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8001/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);

      // Sync Mode if changed by tool
      if (data.current_mode && data.current_mode !== mode) {
        setMode(data.current_mode);
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not connect to Jarvis backend." }]);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = async (newMode: string) => {
    setMode(newMode);
    try {
      await fetch("http://localhost:8001/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode }),
      });
    } catch (e) {
      console.error("Failed to switch mode", e);
    }
  };

  const createMode = async () => {
    if (!newModeName.trim()) return;
    // Just switching to it creates it in our flexible backend logic, 
    // or we can just add it to the list and switch.
    await switchMode(newModeName);
    setAvailableModes(prev => [...new Set([...prev, newModeName])]);
    setNewModeName("");
    setShowAddMode(false);
  };

  const deleteMode = async (modeToDelete: string) => {
    if (!confirm(`Are you sure you want to delete mode '${modeToDelete}' and all its memories?`)) return;

    try {
      await fetch(`http://localhost:8001/modes/${modeToDelete}`, { method: "DELETE" });
      await fetchModes(); // Refresh list associated
    } catch (e) {
      console.error("Failed to delete mode", e);
    }
  };

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">

      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-2">
            <Bot /> Jarvis
          </h1>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Modes</h2>
          {availableModes.map(m => (
            <div key={m} className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${mode === m ? 'bg-blue-900/50 text-blue-200' : 'hover:bg-gray-800 text-gray-400'}`}>
              <div className="flex items-center gap-2 flex-1" onClick={() => switchMode(m)}>
                {m === "Work" ? <Briefcase size={16} /> : m === "Personal" ? <Coffee size={16} /> : <Database size={16} />}
                <span className="truncate">{m}</span>
              </div>
              {m !== "Work" && (
                <button onClick={() => deleteMode(m)} className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity">
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))}

          {showAddMode ? (
            <div className="mt-2 p-2 bg-gray-800 rounded-lg">
              <input
                className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500 mb-2"
                placeholder="Mode Name..."
                value={newModeName}
                onChange={e => setNewModeName(e.target.value)}
                autoFocus
              />
              <div className="flex gap-2">
                <button onClick={createMode} className="flex-1 bg-blue-600 hover:bg-blue-500 py-1 rounded text-xs">Add</button>
                <button onClick={() => setShowAddMode(false)} className="flex-1 bg-gray-700 hover:bg-gray-600 py-1 rounded text-xs">Cancel</button>
              </div>
            </div>
          ) : (
            <button onClick={() => setShowAddMode(true)} className="w-full mt-2 flex items-center gap-2 p-2 rounded-lg border border-dashed border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-500 transition-all text-sm">
              <Plus size={16} /> New Mode
            </button>
          )}
        </div>

        <div className="p-4 border-t border-gray-800">
          <button
            onClick={() => setShowMemory(!showMemory)}
            className={`w-full py-2 px-3 rounded-lg flex items-center justify-center gap-2 text-sm font-medium transition-colors ${showMemory ? 'bg-purple-900/50 text-purple-200' : 'bg-gray-800 hover:bg-gray-700'}`}
          >
            <Database size={16} /> {showMemory ? "Hide Memory" : "View Memory"}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-gray-800 bg-gray-900/50 backdrop-blur flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${mode === "Work" ? "bg-blue-600" : "bg-purple-600"}`}>
              {mode === "Work" ? <Briefcase size={20} /> : <Coffee size={20} />}
            </div>
            <div>
              <h2 className="font-semibold text-lg">{mode} Mode</h2>
              <p className="text-xs text-gray-500">Active context</p>
            </div>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Chat */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Bot size={48} className="mb-4 opacity-50" />
                  <p>Hello! I am Jarvis.</p>
                  <p className="text-sm">Current Mode: <span className="text-blue-400">{mode}</span></p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                >
                  {msg.role !== "user" && (
                    <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mt-1 flex-shrink-0">
                      <Bot size={16} />
                    </div>
                  )}

                  <div
                    className={`p-3 rounded-2xl max-w-[80%] whitespace-pre-wrap ${msg.role === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700"
                      }`}
                  >
                    {msg.content}
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-blue-900 flex items-center justify-center mt-1 flex-shrink-0">
                      <User size={16} />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex justify-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mt-1">
                    <Bot size={16} />
                  </div>
                  <div className="bg-gray-800 p-3 rounded-2xl rounded-bl-none text-gray-400 flex items-center gap-2">
                    <Loader2 className="animate-spin" size={16} />
                    Thinking...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-800 bg-gray-900/80 backdrop-blur">
              <div className="max-w-4xl mx-auto flex gap-2">
                <input
                  className="flex-1 bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 text-gray-100"
                  placeholder={`Message Jarvis in ${mode} mode...`}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="p-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-colors text-white"
                >
                  <Send size={20} />
                </button>
              </div>
            </div>
          </div>

          {/* Memory Panel */}
          {showMemory && (
            <div className="w-80 border-l border-gray-800 bg-gray-900/50 flex flex-col">
              <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <h3 className="font-semibold text-sm uppercase tracking-wide text-gray-400">Memory ({mode})</h3>
                <button onClick={() => setShowMemory(false)} className="text-gray-500 hover:text-white"><X size={16} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {memoryFacts.length === 0 ? (
                  <p className="text-sm text-gray-600 italic">No facts saved for this mode yet.</p>
                ) : (
                  memoryFacts.map((fact, i) => (
                    <div key={i} className="p-3 bg-gray-800 rounded border border-gray-700 text-sm text-gray-300">
                      {fact}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
