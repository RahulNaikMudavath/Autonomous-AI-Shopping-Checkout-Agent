import React, { useState } from 'react';
import { Search, Sparkles, Send, Laptop, Headphones, Smartphone, Monitor } from 'lucide-react';

const QUICK_PROMPTS = [
  { label: "💻 AI/ML Laptop under ₹1.2L", query: "I need a laptop for AI/ML development under ₹1.2 lakh with 32GB RAM and RTX GPU." },
  { label: "🎧 Sony WH-1000XM5 ANC", query: "Find the best noise cancelling headphones under ₹30,000 with 30+ hour battery life." },
  { label: "📱 Flagship Smartphone (5G, 12GB)", query: "I need a flagship 5G smartphone with top tier camera and 12GB RAM under ₹1.2 lakh." },
  { label: "🖥️ 4K 144Hz Gaming Monitor", query: "Find me a 4K 144Hz IPS gaming monitor with 1ms response time under ₹50,000." }
];

export default function ChatInterface({ 
  onSubmitQuery, 
  isLoading = false,
  extractedReqs = null 
}) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim() || isLoading) return;
    onSubmitQuery(query);
  };

  const handleSelectQuickPrompt = (q) => {
    setQuery(q);
    onSubmitQuery(q);
  };

  return (
    <div className="space-y-3.5 max-w-4xl mx-auto">
      {/* Modern Hero Search Bar */}
      <div className="glass-panel p-2 sm:p-3 border-indigo-500/30 shadow-[0_0_50px_rgba(99,102,241,0.15)] focus-within:border-indigo-500 transition-all rounded-2xl bg-slate-950/80">
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <div className="flex items-center gap-2.5 px-3 flex-1">
            <Search className="w-5 h-5 text-indigo-400 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What are you looking for? (e.g. AI/ML laptop with 32GB RAM under ₹1.2L, Sony WH-1000XM5, iPhone 15 Pro)"
              className="w-full bg-transparent border-none text-white text-sm focus:outline-none placeholder-slate-500 py-2"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="btn-primary py-2.5 px-6 rounded-xl flex items-center justify-center gap-2 text-xs font-bold shrink-0 shadow-lg disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isLoading ? "Searching..." : "Shop with AI"}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Sleek Quick Pills */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 text-xs">
        <span className="text-[11px] font-mono text-slate-500 font-bold uppercase tracking-wider shrink-0">
          Try:
        </span>
        {QUICK_PROMPTS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSelectQuickPrompt(p.query)}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-full bg-white/[0.03] hover:bg-indigo-600/20 hover:text-indigo-300 border border-white/10 hover:border-indigo-500/40 text-slate-300 transition-all shrink-0 font-medium text-xs flex items-center gap-1.5"
          >
            <span>{p.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
