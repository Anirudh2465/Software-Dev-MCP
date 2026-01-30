'use client';

import React from 'react';
import { Navbar } from '../components/Navbar';
import { motion } from 'framer-motion';
import { Brain, Cpu, Sparkles, Zap, Globe, Shield } from 'lucide-react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-transparent text-foreground font-sans overflow-x-hidden">
      <Navbar />

      {/* Hero Section */}
      <section className="relative px-6 pt-32 pb-20 md:pt-48 md:pb-32 flex flex-col items-center justify-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="z-10"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
            <span className="text-xs font-medium text-gray-300 tracking-wide uppercase">System Online v2.0</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent drop-shadow-lg">
            Your Digital <span className="text-accent instrument-serif italic">Synapse</span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 mb-10 leading-relaxed">
            An advanced cognitive architecture designed to augment your workflow with persistent memory, dynamic personas, and deep system integration.
          </p>

          <div className="flex flex-col md:flex-row gap-4 justify-center">
            <Link href="/chat">
              <button className="px-8 py-4 rounded-xl bg-action hover:bg-accent text-white font-semibold transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] active:scale-95 flex items-center gap-2">
                <Zap size={20} className="fill-current" />
                Launch System
              </button>
            </Link>
            <Link href="/signup">
              <button className="px-8 py-4 rounded-xl bg-surface/50 border border-white/10 hover:bg-white/5 text-white font-medium transition-all backdrop-blur-md active:scale-95">
                Request Access
              </button>
            </Link>
          </div>
        </motion.div>

        {/* Decorative Elements */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent/20 rounded-full blur-[120px] pointer-events-none opacity-40 animate-pulse"></div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-20 relative z-10">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon={Brain}
            title="Semantic Memory"
            desc="Jarvis remembers facts, preferences, and context across all your conversations, building a knowledge base that grows with you."
            delay={0}
          />
          <FeatureCard
            icon={Globe}
            title="Dynamic Personas"
            desc="Switch instantly between a clean Generalist, a rigorous Systems Architect, or a precise Coder to match your current headspace."
            delay={0.1}
          />
          <FeatureCard
            icon={Shield}
            title="Local Execution"
            desc="Built for privacy and speed. Your data stays within your local environment, powered by optimized local LLMs."
            delay={0.2}
          />
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-10 text-center text-gray-600 text-sm">
        <p>&copy; 2026 AutoBots. All systems nominal.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc, delay }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
      className="group p-8 rounded-2xl bg-surface/40 backdrop-blur-md border border-white/5 hover:bg-surface/60 hover:border-white/10 transition-all hover:-translate-y-1"
    >
      <div className="w-12 h-12 rounded-lg bg-surface/80 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-inner border border-white/5">
        <Icon size={24} className="text-accent" />
      </div>
      <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
      <p className="text-gray-400 leading-relaxed text-sm">
        {desc}
      </p>
    </motion.div>
  );
}
