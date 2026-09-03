import React, { useState } from 'react';
import { Network, Terminal, Play, CheckCircle2, Code2, Globe, Layers, ArrowRight } from 'lucide-react';

export default function ProtocolExplorer() {
  const [selectedTool, setSelectedTool] = useState("search_products");
  const [toolArgs, setToolArgs] = useState(JSON.stringify({
    query: "RTX 4070 32GB",
    max_price_inr: 120000,
    min_ram_gb: 32
  }, null, 2));
  const [toolResponse, setToolResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const [activeTab, setActiveTab] = useState("mcp"); // "mcp" or "ucp"

  const handleExecuteTool = async () => {
    setLoading(true);
    try {
      const parsedArgs = JSON.parse(toolArgs);
      const res = await fetch('http://localhost:8000/api/mcp/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: selectedTool,
          arguments: parsedArgs
        })
      });
      const data = await res.json();
      setToolResponse(data);
    } catch (err) {
      setToolResponse({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (toolName, defaultJson) => {
    setSelectedTool(toolName);
    setToolArgs(JSON.stringify(defaultJson, null, 2));
    setToolResponse(null);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Network className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              Commerce Protocol &amp; MCP Tool Interface
            </h2>
            <p className="text-xs text-slate-400">
              Layer 3: Universal Commerce Protocol (UCP v1.0) &amp; Model Context Protocol (MCP) Server
            </p>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex bg-black/40 p-1 rounded-lg border border-white/10 text-xs font-semibold">
          <button 
            onClick={() => setActiveTab("mcp")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'mcp' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Model Context Protocol (MCP)
          </button>
          <button 
            onClick={() => setActiveTab("ucp")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'ucp' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Universal Commerce (UCP v1)
          </button>
        </div>
      </div>

      {activeTab === 'mcp' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tool Selector */}
          <div className="glass-panel p-5 space-y-3 border-white/10">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-400" />
              Available MCP Tools
            </h3>

            <div className="space-y-1.5">
              <button 
                onClick={() => loadPreset("search_products", { query: "RTX 4070 32GB", max_price_inr: 120000, min_ram_gb: 32 })}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border ${
                  selectedTool === 'search_products' ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200' : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20'
                }`}
              >
                <div className="font-bold">search_products</div>
                <div className="text-[10px] text-slate-400 font-sans mt-0.5">Multi-merchant catalog query</div>
              </button>

              <button 
                onClick={() => loadPreset("calculate_value_score", { product_id: "prod_laptop_b_rog", budget_max_inr: 120000 })}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border ${
                  selectedTool === 'calculate_value_score' ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200' : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20'
                }`}
              >
                <div className="font-bold">calculate_value_score</div>
                <div className="text-[10px] text-slate-400 font-sans mt-0.5">MCDA score &amp; breakdown</div>
              </button>

              <button 
                onClick={() => loadPreset("verify_spending_policy", { product_id: "prod_laptop_b_rog" })}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border ${
                  selectedTool === 'verify_spending_policy' ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200' : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20'
                }`}
              >
                <div className="font-bold">verify_spending_policy</div>
                <div className="text-[10px] text-slate-400 font-sans mt-0.5">Guardrail limits &amp; HITL check</div>
              </button>

              <button 
                onClick={() => loadPreset("execute_checkout_order", { product_id: "prod_laptop_b_rog", shipping_address: "Rahul N., Tech Park Bangalore" })}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border ${
                  selectedTool === 'execute_checkout_order' ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200' : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20'
                }`}
              >
                <div className="font-bold">execute_checkout_order</div>
                <div className="text-[10px] text-slate-400 font-sans mt-0.5">Tokenized purchase &amp; audit stamp</div>
              </button>

              <button 
                onClick={() => loadPreset("track_order_status", { order_id: "ORD_SAMPLE" })}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border ${
                  selectedTool === 'track_order_status' ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200' : 'bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20'
                }`}
              >
                <div className="font-bold">track_order_status</div>
                <div className="text-[10px] text-slate-400 font-sans mt-0.5">Real-time delivery status</div>
              </button>
            </div>
          </div>

          {/* Interactive Request & Response Console */}
          <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                <span className="font-mono text-xs font-bold text-white">Tool: {selectedTool}</span>
              </div>

              <button 
                onClick={handleExecuteTool}
                disabled={loading}
                className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                {loading ? "Executing..." : "Call MCP Tool"}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Arguments JSON Editor */}
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  Arguments (JSON):
                </label>
                <textarea 
                  value={toolArgs}
                  onChange={(e) => setToolArgs(e.target.value)}
                  rows={10}
                  className="form-input font-mono text-xs text-indigo-200 bg-black/50"
                />
              </div>

              {/* Execution Result */}
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  Response Output:
                </label>
                <div className="p-3 rounded-lg bg-black/60 border border-white/10 h-52 overflow-y-auto text-xs font-mono text-emerald-300">
                  {toolResponse ? (
                    <pre>{JSON.stringify(toolResponse, null, 2)}</pre>
                  ) : (
                    <div className="text-slate-500 italic mt-16 text-center">
                      Click "Call MCP Tool" to execute.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* UCP v1.0 Explorer View */
        <div className="glass-panel p-6 space-y-5 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Globe className="w-4 h-4 text-cyan-400" />
              Universal Commerce Protocol (UCP v1.0) Endpoints
            </h3>
            <span className="badge badge-cyan text-xs">Standard RFC</span>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="badge badge-emerald text-[10px]">GET</span>
                <span className="text-white font-bold">/ucp/v1/merchants</span>
                <span className="text-slate-400 font-sans text-[11px]">Merchant discovery &amp; trust ratings</span>
              </div>
              <span className="text-slate-500">200 OK</span>
            </div>

            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="badge badge-indigo text-[10px]">POST</span>
                <span className="text-white font-bold">/ucp/v1/catalog/search</span>
                <span className="text-slate-400 font-sans text-[11px]">Multi-merchant federated search</span>
              </div>
              <span className="text-slate-500">200 OK</span>
            </div>

            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="badge badge-indigo text-[10px]">POST</span>
                <span className="text-white font-bold">/ucp/v1/cart/quote</span>
                <span className="text-slate-400 font-sans text-[11px]">Tokenized checkout pricing quote</span>
              </div>
              <span className="text-slate-500">200 OK</span>
            </div>

            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="badge badge-indigo text-[10px]">POST</span>
                <span className="text-white font-bold">/ucp/v1/checkout/execute</span>
                <span className="text-slate-400 font-sans text-[11px]">Autonomous payment authorization</span>
              </div>
              <span className="text-slate-500">200 OK</span>
            </div>

            <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="badge badge-emerald text-[10px]">GET</span>
                <span className="text-white font-bold">/ucp/v1/orders/&#123;id&#125;</span>
                <span className="text-slate-400 font-sans text-[11px]">Lifecycle &amp; delivery tracking</span>
              </div>
              <span className="text-slate-500">200 OK</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
