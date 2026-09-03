import React, { useState, useEffect } from 'react';
import { 
  Settings, Key, ShieldCheck, CheckCircle2, 
  ExternalLink, X, Save, Sparkles, Globe, CreditCard, Database, Cpu 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function ApiSettingsModal({ isOpen, onClose, onSaveSuccess }) {
  const [settings, setSettings] = useState({
    openai_api_key: '',
    gemini_api_key: '',
    anthropic_api_key: '',
    default_llm_provider: 'openai',
    serpapi_api_key: '',
    tavily_api_key: '',
    brave_api_key: '',
    live_discovery_mode: 'auto',
    stripe_secret_key: '',
    stripe_publishable_key: '',
    razorpay_key_id: '',
    razorpay_key_secret: '',
    langfuse_public_key: '',
    langfuse_secret_key: ''
  });

  const [activeConfigStatus, setActiveConfigStatus] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('llm'); // 'llm' | 'search' | 'payments' | 'db'

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/settings`);
      if (res.ok) {
        setActiveConfigStatus(await res.json());
      }
    } catch (err) {
      console.error("Settings fetch error:", err);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload = {};
      Object.keys(settings).forEach(k => {
        if (settings[k]) payload[k] = settings[k];
      });

      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        await fetchSettings();
        if (onSaveSuccess) onSaveSuccess("API keys and live integrations updated successfully!");
        onClose();
      }
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-2xl border-white/20 bg-slate-950 p-6 space-y-6 shadow-2xl relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-heading">
                Live Real-World API Keys &amp; Integrations
              </h3>
              <p className="text-xs text-slate-400">
                Connect your real OpenAI, Gemini, SerpAPI, Tavily, Stripe, or Razorpay credentials
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-white/10 pb-2 text-xs font-mono">
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'llm' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>LLM Providers</span>
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'search' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Live Web Search</span>
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'payments' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <CreditCard className="w-3.5 h-3.5" />
            <span>Payment Gateways</span>
          </button>

          <button
            onClick={() => setActiveTab('db')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeTab === 'db' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>DB &amp; Tracing</span>
          </button>
        </div>

        {/* Form Inputs */}
        <form onSubmit={handleSave} className="space-y-4 font-mono text-xs">
          {/* TAB 1: LLM KEYS */}
          {activeTab === 'llm' && (
            <div className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-slate-300 font-bold flex justify-between">
                  <span>OpenAI API Key (GPT-4o)</span>
                  {activeConfigStatus?.openai_api_key_configured && (
                    <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Configured
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  placeholder="sk-proj-..."
                  value={settings.openai_api_key}
                  onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-bold flex justify-between">
                  <span>Google Gemini API Key (Gemini 1.5 Pro)</span>
                  {activeConfigStatus?.gemini_api_key_configured && (
                    <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Configured
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  placeholder="AIzaSy..."
                  value={settings.gemini_api_key}
                  onChange={(e) => setSettings({ ...settings, gemini_api_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-bold flex justify-between">
                  <span>Anthropic API Key (Claude 3.5 Sonnet)</span>
                  {activeConfigStatus?.anthropic_api_key_configured && (
                    <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Configured
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  placeholder="sk-ant-..."
                  value={settings.anthropic_api_key}
                  onChange={(e) => setSettings({ ...settings, anthropic_api_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          )}

          {/* TAB 2: LIVE SEARCH */}
          {activeTab === 'search' && (
            <div className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-slate-300 font-bold flex justify-between">
                  <span>SerpAPI / Google Shopping Key (Amazon &amp; Flipkart Real-Time)</span>
                  {activeConfigStatus?.serpapi_api_key_configured && (
                    <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Configured
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  placeholder="Enter SerpAPI key..."
                  value={settings.serpapi_api_key}
                  onChange={(e) => setSettings({ ...settings, serpapi_api_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-bold flex justify-between">
                  <span>Tavily AI Search API Key</span>
                  {activeConfigStatus?.tavily_api_key_configured && (
                    <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Configured
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  placeholder="tvly-..."
                  value={settings.tavily_api_key}
                  onChange={(e) => setSettings({ ...settings, tavily_api_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-slate-300 text-[11px]">
                💡 <strong>Zero-Config Built-in:</strong> AgentCart includes built-in real-world web commerce intelligence that discovers products out-of-the-box even without a SerpAPI key!
              </div>
            </div>
          )}

          {/* TAB 3: PAYMENTS */}
          {activeTab === 'payments' && (
            <div className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-slate-300 font-bold">Stripe Secret Key (Test or Live)</label>
                <input
                  type="password"
                  placeholder="sk_test_..."
                  value={settings.stripe_secret_key}
                  onChange={(e) => setSettings({ ...settings, stripe_secret_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-bold">Razorpay Key ID</label>
                <input
                  type="text"
                  placeholder="rzp_test_..."
                  value={settings.razorpay_key_id}
                  onChange={(e) => setSettings({ ...settings, razorpay_key_id: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          )}

          {/* TAB 4: DB & TRACING */}
          {activeTab === 'db' && (
            <div className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-slate-300 font-bold">Langfuse Public Key</label>
                <input
                  type="text"
                  placeholder="pk-lf-..."
                  value={settings.langfuse_public_key}
                  onChange={(e) => setSettings({ ...settings, langfuse_public_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-bold">Langfuse Secret Key</label>
                <input
                  type="password"
                  placeholder="sk-lf-..."
                  value={settings.langfuse_secret_key}
                  onChange={(e) => setSettings({ ...settings, langfuse_secret_key: e.target.value })}
                  className="w-full bg-black/60 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary py-2 px-4 text-xs font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="btn-primary py-2 px-5 text-xs font-bold flex items-center gap-1.5 shadow-lg"
            >
              <Save className="w-3.5 h-3.5" />
              {isSaving ? "Saving..." : "Save Configuration"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
