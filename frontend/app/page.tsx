"use client";
import { useState, useEffect, useRef } from "react";
import { Send, User, Bot, Briefcase, Coffee, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("Work");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not connect to Jarvis backend." }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = async () => {
    const newMode = mode === "Work" ? "Personal" : "Work";
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

  return (
    <main className="flex min-h-screen flex-col bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-full ${mode === "Work" ? "bg-blue-600" : "bg-purple-600"}`}>
            {mode === "Work" ? <Briefcase size={20} /> : <Coffee size={20} />}
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Jarvis
          </h1>
        </div>

        <button
          onClick={toggleMode}
          className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors text-sm font-medium flex items-center gap-2"
        >
          Switch to {mode === "Work" ? "Personal" : "Work"}
        </button>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 max-w-4xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 mt-20">
            <Bot size={48} className="mb-4 opacity-50" />
            <p>Hello! I am Jarvis. How can I help you today?</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"
              }`}
          >
            {msg.role !== "user" && (
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mt-1">
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
              <div className="w-8 h-8 rounded-full bg-blue-900 flex items-center justify-center mt-1">
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

      {/* Input Area */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/80 backdrop-blur sticky bottom-0">
        <div className="max-w-4xl mx-auto flex gap-2">
          <input
            className="flex-1 bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 text-gray-100"
            placeholder="Type a message..."
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
    </main>
  );
}
