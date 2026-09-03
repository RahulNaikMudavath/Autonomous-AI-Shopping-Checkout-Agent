import React, { useState, useEffect } from 'react';
import { 
  Brain, User, ShoppingCart, Database, Search, Plus, 
  CheckCircle2, Sparkles, Sliders, History, DollarSign, Cpu, Tag, ArrowRight 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const VECTOR_PRESETS = [
  "I prefer lightweight laptops",
  "I usually buy Logitech peripherals",
  "Don't recommend refurbished products",
  "Always check for 3-year warranty",
  "Prioritize matte display finish"
];

export default function MemoryConsole() {
  const [activeTierTab, setActiveTierTab] = useState('semantic'); // 'semantic' | 'profile' | 'transactions' | 'working'
  const [memoryOverview, setMemoryOverview] = useState(null);
  
  // Semantic Vector Search State
  const [semanticQuery, setSemanticQuery] = useState(VECTOR_PRESETS[0]);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // New Memory Ingestion State
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newMemoryCategory, setNewMemoryCategory] = useState('user_preference');
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    fetchMemoryOverview();
    handleSearchSemantic(VECTOR_PRESETS[0]);
  }, []);

  const fetchMemoryOverview = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/overview`);
      if (res.ok) {
        setMemoryOverview(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchSemantic = async (queryText) => {
    setIsSearching(true);
    setSemanticQuery(queryText);
    try {
      const res = await fetch(`${API_BASE}/api/memory/semantic/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, top_k: 3 })
      });
      if (res.ok) {
        setSearchResults(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;
    setIsAdding(true);
    try {
      const res = await fetch(`${API_BASE}/api/memory/semantic/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newMemoryText, category: newMemoryCategory })
      });
      if (res.ok) {
        setNewMemoryText('');
        fetchMemoryOverview();
        handleSearchSemantic(newMemoryText);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-purple-500/30 bg-gradient-to-r from-slate-900 via-purple-950/40 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              10. Multi-Tier Memory Subsystem
            </h2>
            <p className="text-xs text-slate-400">
              Profile preferences • Transaction histories • Working state • Vector DB semantic embeddings
            </p>
          </div>
        </div>

        {/* Tier Switcher Pills */}
        <div className="flex items-center gap-1 bg-white/[0.04] p-1 rounded-xl border border-white/10 text-xs font-mono">
          <button
            onClick={() => setActiveTierTab('semantic')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTierTab === 'semantic' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Tier 4: Vector DB
          </button>
          <button
            onClick={() => setActiveTierTab('profile')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTierTab === 'profile' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Tier 1: Profile
          </button>
          <button
            onClick={() => setActiveTierTab('transactions')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTierTab === 'transactions' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Tier 2: Transactions
          </button>
          <button
            onClick={() => setActiveTierTab('working')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTierTab === 'working' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Tier 3: Working State
          </button>
        </div>
      </div>

      {/* TIER 4: SEMANTIC VECTOR MEMORY (VECTOR DB) */}
      {activeTierTab === 'semantic' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Search & Query Testing */}
            <div className="glass-panel p-5 space-y-4 border-white/10">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Search className="w-4 h-4 text-purple-400" />
                Query Vector Database
              </h3>

              <div className="space-y-2">
                <label className="block text-slate-400 font-mono text-[11px]">Quick Query Presets:</label>
                <div className="flex flex-wrap gap-1.5">
                  {VECTOR_PRESETS.map((preset) => (
                    <button
                      key={preset}
                      onClick={() => handleSearchSemantic(preset)}
                      className={`text-[11px] px-2.5 py-1 rounded-lg border font-mono transition-all text-left ${
                        semanticQuery === preset
                          ? 'bg-purple-600 border-purple-400 text-white shadow-md'
                          : 'bg-white/[0.02] border-white/10 text-slate-300 hover:border-white/30'
                      }`}
                    >
                      "{preset}"
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 pt-2">
                <label className="block text-slate-400 font-mono text-[11px]">Custom Semantic Query:</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={semanticQuery}
                    onChange={(e) => setSemanticQuery(e.target.value)}
                    placeholder="e.g. lightweight portable laptop"
                    className="form-input text-xs font-mono flex-1"
                  />
                  <button
                    onClick={() => handleSearchSemantic(semanticQuery)}
                    disabled={isSearching}
                    className="btn-primary bg-purple-600 hover:bg-purple-500 text-xs px-3 font-mono font-bold"
                  >
                    {isSearching ? "Searching..." : "Search"}
                  </button>
                </div>
              </div>

              {/* Add New Memory Form */}
              <form onSubmit={handleAddMemory} className="pt-4 border-t border-white/10 space-y-2.5">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Plus className="w-3.5 h-3.5 text-emerald-400" />
                  Ingest New Semantic Preference
                </h4>
                <input
                  type="text"
                  value={newMemoryText}
                  onChange={(e) => setNewMemoryText(e.target.value)}
                  placeholder="e.g. Always check for Thunderbolt 4..."
                  className="form-input text-xs font-mono w-full"
                />
                <button
                  type="submit"
                  disabled={isAdding || !newMemoryText.trim()}
                  className="w-full btn-secondary text-xs py-2 font-mono font-bold text-slate-200"
                >
                  {isAdding ? "Ingesting..." : "+ Ingest to Vector Store"}
                </button>
              </form>
            </div>

            {/* Search Results & Similarity Rankings */}
            <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Database className="w-4 h-4 text-cyan-400" />
                  Top-k Semantic Vector Matches (Cosine Similarity)
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {searchResults.length} matches retrieved
                </span>
              </div>

              <div className="space-y-3">
                {searchResults.map((res, idx) => (
                  <div key={res.memory.id} className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-purple-300 font-mono">
                        #{idx + 1} Match ID: {res.memory.id} ({res.memory.category})
                      </span>
                      <span className="badge badge-purple text-xs font-mono font-bold">
                        Sim: {(res.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>

                    <p className="text-xs text-white font-medium">
                      "{res.memory.content}"
                    </p>

                    {/* Similarity Bar */}
                    <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full"
                        style={{ width: `${Math.min(100, res.similarity_score * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TIER 1: USER PROFILE MEMORY */}
      {activeTierTab === 'profile' && memoryOverview?.tier_1_user_profile && (
        <div className="glass-panel p-6 border-white/10 space-y-5 animate-in fade-in duration-200">
          <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
            <User className="w-4 h-4 text-indigo-400" />
            Tier 1: User Profile Preferences Memory
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="text-slate-400 font-bold">Preferred Brands:</div>
              <div className="flex flex-wrap gap-1.5">
                {memoryOverview.tier_1_user_profile.preferred_brands.map((b) => (
                  <span key={b} className="badge badge-indigo text-xs">{b}</span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="text-slate-400 font-bold">Category Budgets:</div>
              {Object.entries(memoryOverview.tier_1_user_profile.category_budgets).map(([cat, amt]) => (
                <div key={cat} className="flex justify-between text-slate-300">
                  <span className="capitalize">{cat}:</span>
                  <span className="text-emerald-400 font-bold">₹{Number(amt).toLocaleString()}</span>
                </div>
              ))}
            </div>

            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="text-slate-400 font-bold">Size &amp; Form Constraints:</div>
              {Object.entries(memoryOverview.tier_1_user_profile.sizes).map(([k, v]) => (
                <div key={k} className="flex justify-between text-slate-300">
                  <span className="capitalize">{k.replace('_', ' ')}:</span>
                  <span className="text-cyan-300">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TIER 2: TRANSACTION MEMORY */}
      {activeTierTab === 'transactions' && memoryOverview?.tier_2_transactions && (
        <div className="glass-panel p-6 border-white/10 space-y-5 animate-in fade-in duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              Tier 2: Transaction &amp; Spending Memory
            </h3>
            <span className="badge badge-emerald text-xs font-mono">
              Lifetime Spend: ₹{Number(memoryOverview.tier_2_transactions.total_lifetime_spend_inr).toLocaleString()}
            </span>
          </div>

          <div className="space-y-2.5">
            {memoryOverview.tier_2_transactions.recent_transactions.map((tx) => (
              <div key={tx.order_id} className="p-3.5 rounded-xl bg-black/40 border border-white/5 flex flex-col md:flex-row items-start md:items-center justify-between gap-2 text-xs font-mono">
                <div>
                  <div className="font-bold text-white">{tx.item_title}</div>
                  <div className="text-[11px] text-slate-400">
                    Order ID: {tx.order_id} • Merchant: {tx.merchant_name}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-emerald-400 font-bold">₹{tx.amount_inr.toLocaleString()}</span>
                  <span className={`badge text-[10px] py-0 px-2 ${
                    tx.status === 'DELIVERED' ? 'badge-emerald' : 'badge-rose'
                  }`}>
                    {tx.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TIER 3: WORKING STATE MEMORY */}
      {activeTierTab === 'working' && memoryOverview?.tier_3_working_state && (
        <div className="glass-panel p-6 border-white/10 space-y-5 animate-in fade-in duration-200">
          <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Tier 3: Agent Working Memory &amp; DAG State
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="text-slate-400 font-bold">Active Episodic Task:</div>
              <div className="text-white">{memoryOverview.tier_3_working_state.active_task}</div>
              <div className="text-slate-300">DAG Stage: <span className="text-cyan-400">{memoryOverview.tier_3_working_state.current_dag_stage}</span></div>
              <div className="text-slate-300">Active Mandate: <span className="text-purple-300">{memoryOverview.tier_3_working_state.current_delegated_mandate_id}</span></div>
            </div>

            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="text-slate-400 font-bold">Working Scratchpad:</div>
              <pre className="text-[11px] text-cyan-300 bg-black/60 p-2.5 rounded border border-white/5 overflow-x-auto">
                {JSON.stringify(memoryOverview.tier_3_working_state.scratchpad_notes, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
