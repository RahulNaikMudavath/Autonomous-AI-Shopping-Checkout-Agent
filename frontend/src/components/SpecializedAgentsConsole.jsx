import React, { useState } from 'react';
import { 
  Puzzle, Play, CheckCircle2, ArrowRight, Code, 
  Store, Terminal, Sparkles, Database, ShieldCheck 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function SpecializedAgentsConsole() {
  const [activeSection, setActiveSection] = useState('intent'); // 'intent' | 'planner' | 'merchants'

  // Agent 1 Intent State
  const [intentInput, setIntentInput] = useState("I need a laptop for coding and AI under 1.2L");
  const [intentOutput, setIntentOutput] = useState(null);
  const [isParsingIntent, setIsParsingIntent] = useState(false);

  // Agent 2 Planner State
  const [dagInput, setDagInput] = useState("I need a laptop for coding and AI under 1.2L");
  const [dagResult, setDagResult] = useState(null);
  const [isExecutingDag, setIsExecutingDag] = useState(false);

  // Agent 3 Merchant APIs State
  const [selectedMerchant, setSelectedMerchant] = useState('a');
  const [merchantData, setMerchantData] = useState(null);
  const [isLoadingMerchant, setIsLoadingMerchant] = useState(false);

  const handleParseIntent = async () => {
    setIsParsingIntent(true);
    try {
      const res = await fetch(`${API_BASE}/api/agents/intent/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: intentInput })
      });
      if (res.ok) {
        const data = await res.json();
        setIntentOutput(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsParsingIntent(false);
    }
  };

  const handleExecuteDag = async () => {
    setIsExecutingDag(true);
    try {
      const res = await fetch(`${API_BASE}/api/agents/planner/execute-dag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: dagInput })
      });
      if (res.ok) {
        const data = await res.json();
        setDagResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsExecutingDag(false);
    }
  };

  const handleFetchMerchantApi = async (merchantKey) => {
    setSelectedMerchant(merchantKey);
    setIsLoadingMerchant(true);
    let endpoint = '/api/merchants/a/catalog';
    if (merchantKey === 'b') endpoint = '/api/merchants/b/search';
    if (merchantKey === 'c') endpoint = '/api/merchants/c/products';
    if (merchantKey === 'd') endpoint = '/api/merchants/d/enterprise-catalog';

    try {
      const res = await fetch(`${API_BASE}${endpoint}`);
      if (res.ok) {
        const data = await res.json();
        setMerchantData(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingMerchant(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="glass-panel p-6 border-indigo-500/30 bg-gradient-to-r from-slate-900 via-purple-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <Puzzle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              3. Specialized Agents Console
            </h2>
            <p className="text-xs text-slate-400">
              Agent 1 (Intent Agent), Agent 2 (Planning Agent DAG), Agent 3 (Discovery &amp; Merchant REST APIs)
            </p>
          </div>
        </div>

        {/* Section Tabs */}
        <div className="flex bg-black/40 p-1 rounded-xl border border-white/10 text-xs font-semibold">
          <button 
            onClick={() => setActiveSection('intent')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeSection === 'intent' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Agent 1: Intent Agent
          </button>
          <button 
            onClick={() => setActiveSection('planner')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeSection === 'planner' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Agent 2: Planning DAG
          </button>
          <button 
            onClick={() => {
              setActiveSection('merchants');
              if (!merchantData) handleFetchMerchantApi('a');
            }}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeSection === 'merchants' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Agent 3: Merchant APIs
          </button>
        </div>
      </div>

      {/* SECTION 1: AGENT 1 INTENT AGENT */}
      {activeSection === 'intent' && (
        <div className="glass-panel p-6 space-y-5 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Agent 1 — Intent Agent
              </h3>
              <p className="text-xs text-slate-400">
                Transforms unstructured natural language query into exact typed structured state
              </p>
            </div>
            <span className="badge badge-indigo text-xs font-mono">NLP State Extractor</span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Input Query Prompt:
              </label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={intentInput}
                  onChange={(e) => setIntentInput(e.target.value)}
                  className="form-input text-xs font-mono"
                  placeholder="e.g. I need a laptop for coding and AI under 1.2L"
                />
                <button 
                  onClick={handleParseIntent}
                  disabled={isParsingIntent}
                  className="btn-primary text-xs py-2 px-4 shrink-0 font-semibold"
                >
                  {isParsingIntent ? "Extracting..." : "Parse to State"}
                </button>
              </div>
            </div>

            {/* Quick preset buttons */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-slate-500 text-[11px] font-semibold">Test Presets:</span>
              <button 
                onClick={() => setIntentInput("I need a laptop for coding and AI under 1.2L")}
                className="text-[11px] bg-white/5 hover:bg-white/10 px-2.5 py-1 rounded text-slate-300"
              >
                Core Prompt: "under 1.2L for coding & AI"
              </button>
              <button 
                onClick={() => setIntentInput("Looking for 64GB RAM laptop under 1.8 lakh with 2TB storage and highest performance")}
                className="text-[11px] bg-white/5 hover:bg-white/10 px-2.5 py-1 rounded text-slate-300"
              >
                High-Spec: "64GB RAM, 2TB storage"
              </button>
            </div>

            {/* Structured State JSON Output */}
            {intentOutput && (
              <div className="p-4 rounded-xl bg-black/60 border border-indigo-500/30 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-cyan-300 font-bold flex items-center gap-1.5">
                    <Code className="w-3.5 h-3.5" />
                    Exact Structured State JSON
                  </span>
                  <span className="badge badge-emerald text-[10px]">Validated Schema</span>
                </div>
                <pre className="text-xs font-mono text-emerald-300 overflow-x-auto p-2">
                  {JSON.stringify(intentOutput, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 2: AGENT 2 PLANNING AGENT DAG */}
      {activeSection === 'planner' && (
        <div className="glass-panel p-6 space-y-5 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-purple-400" />
                Agent 2 — Planning Agent (8-Step Commerce DAG)
              </h3>
              <p className="text-xs text-slate-400">
                Executes the deterministic commerce plan with stage telemetry
              </p>
            </div>
            <button 
              onClick={handleExecuteDag}
              disabled={isExecutingDag}
              className="btn-primary bg-purple-600 hover:bg-purple-500 text-xs py-1.5 px-3 flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {isExecutingDag ? "Executing DAG..." : "Run 8-Step Commerce DAG"}
            </button>
          </div>

          {/* DAG Visual Flow */}
          <div className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              {[
                "1. Search merchants",
                "2. Normalize results",
                "3. Filter constraints",
                "4. Rank candidates",
                "5. Check availability",
                "6. Create cart",
                "7. Calculate final price",
                "8. Check authorization"
              ].map((stepTitle, idx) => {
                const executedStep = dagResult?.steps?.find(s => s.step_number === idx + 1);
                const isDone = !!executedStep;

                return (
                  <div 
                    key={idx}
                    className={`p-3.5 rounded-xl border transition-all ${
                      isDone 
                        ? 'bg-purple-950/40 border-purple-500/50 text-white shadow-md' 
                        : 'bg-white/[0.02] border-white/5 text-slate-500'
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold font-mono">
                      <span>{stepTitle}</span>
                      {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                    </div>
                    {isDone && (
                      <p className="text-[11px] text-slate-300 mt-2 line-clamp-2">
                        {executedStep.output_summary}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Output Inspection */}
            {dagResult && (
              <div className="mt-4 p-4 rounded-xl bg-black/40 border border-white/10 space-y-3 text-xs">
                <div className="flex items-center justify-between font-mono">
                  <span className="font-bold text-slate-200">DAG Final Outcome:</span>
                  <span className="text-emerald-400 font-bold">
                    Top Pick: {dagResult.top_candidate?.title} (₹{dagResult.top_candidate?.price_inr.toLocaleString()})
                  </span>
                </div>
                <div className="text-slate-400 text-[11px] font-mono">
                  Quote ID: {dagResult.quote?.quote_id} • Total: ₹{dagResult.quote?.amount_inr.toLocaleString()} • Authorization: Verified
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 3: AGENT 3 DISCOVERY AGENT & MERCHANT APIS */}
      {activeSection === 'merchants' && (
        <div className="glass-panel p-6 space-y-5 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Store className="w-4 h-4 text-cyan-400" />
                Agent 3 — Discovery Agent &amp; Merchant Commerce REST APIs
              </h3>
              <p className="text-xs text-slate-400">
                Live inspection of standalone Merchant A, B, C, and D commerce services (No scraping)
              </p>
            </div>
            <span className="badge badge-cyan text-xs">4 Services Online</span>
          </div>

          {/* Merchant API Selector */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'a', name: 'Merchant A (TechHub)', spec: 'Workstations & GPUs', path: '/api/merchants/a/catalog' },
              { key: 'b', name: 'Merchant B (ElectroBazaar)', spec: 'Consumer Tech', path: '/api/merchants/b/search' },
              { key: 'c', name: 'Merchant C (OmniStore)', spec: 'Mass Retail', path: '/api/merchants/c/products' },
              { key: 'd', name: 'Merchant D (ProHardware)', spec: 'Enterprise OEM', path: '/api/merchants/d/enterprise-catalog' }
            ].map((m) => (
              <button
                key={m.key}
                onClick={() => handleFetchMerchantApi(m.key)}
                className={`p-3 rounded-xl border text-left text-xs transition-all ${
                  selectedMerchant === m.key 
                    ? 'bg-cyan-950/60 border-cyan-500/60 text-white shadow-[0_0_15px_rgba(6,182,212,0.25)]' 
                    : 'bg-white/[0.02] border-white/5 text-slate-400 hover:border-white/20'
                }`}
              >
                <div className="font-bold text-slate-200">{m.name}</div>
                <div className="text-[10px] text-cyan-400 font-mono mt-0.5">{m.path}</div>
                <div className="text-[10px] text-slate-500 mt-1">{m.spec}</div>
              </button>
            ))}
          </div>

          {/* Raw Merchant API Response Console */}
          <div className="p-4 rounded-xl bg-black/60 border border-cyan-500/30 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono text-cyan-300 font-bold flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5" />
                Live Merchant Service Response Payload
              </span>
              <span className="text-slate-400 font-mono text-[11px]">HTTP 200 OK</span>
            </div>

            <div className="max-h-72 overflow-y-auto">
              {isLoadingMerchant ? (
                <div className="text-slate-500 text-xs italic p-4 text-center">Fetching Merchant API payload...</div>
              ) : (
                <pre className="text-xs font-mono text-cyan-200 p-2">
                  {JSON.stringify(merchantData, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
