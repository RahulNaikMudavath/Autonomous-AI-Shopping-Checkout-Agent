import React, { useState, useEffect } from 'react';
import { 
  Building2, Server, Database, Cpu, Network, Shield, 
  GitBranch, Box, CheckCircle2, ArrowRight, Zap, RefreshCw, Layers, ExternalLink, Code 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function SystemArchitectureMap() {
  const [infraData, setInfraData] = useState(null);
  const [selectedNode, setSelectedNode] = useState('supervisor');
  const [activeTab, setActiveTab] = useState('topology'); // 'topology' | 'infrastructure' | 'cicd'

  useEffect(() => {
    fetchInfraStatus();
  }, []);

  const fetchInfraStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/infrastructure/status`);
      if (res.ok) {
        setInfraData(await res.json());
      }
    } catch (err) {
      console.error("Infrastructure status fetch error:", err);
    }
  };

  const nodeExplanations = {
    user: {
      title: "1. User Interface (Next.js / React)",
      layer: "Layer 1: User Experience",
      desc: "Conversational Copilot, live reasoning trace, side-by-side MCDA comparison matrix, and instant checkout triggers with Human-in-the-Loop authorization modals."
    },
    gateway: {
      title: "2. FastAPI API Gateway",
      layer: "Layer 1 & 3: Gateway & Transport",
      desc: "High-throughput asynchronous REST gateway routing client requests, managing session contexts, and hosting MCP tool servers & UCP endpoints."
    },
    supervisor: {
      title: "3. LangGraph Agent Supervisor",
      layer: "Layer 2: Agent Intelligence",
      desc: "State machine orchestrator managing dynamic execution DAGs, subagent handoffs, multi-tier memory fusion, and distributed failure recovery."
    },
    intent: {
      title: "4. Intent Agent",
      layer: "Layer 2: Specialized Subagent",
      desc: "Converts natural language input into deterministic typed schemas (category, budget ceiling, RAM/SSD/GPU constraints, and optimization priority)."
    },
    discovery: {
      title: "5. Discovery Agent & Merchant Gateway",
      layer: "Layer 3 & 4: Protocol & Infrastructure",
      desc: "Parallel broadcasting across Merchant A, B, C, D APIs via REST, MCP tools, and UCP-compatible envelopes with automatic untrusted content sanitization."
    },
    ranking: {
      title: "6. Ranking Agent & Vector Memory",
      layer: "Layer 2: Multi-Criteria Evaluation",
      desc: "Multi-Criteria Decision Analysis (MCDA) normalized value scoring augmented with cosine similarity retrieval from pgvector user preference memory."
    },
    cart: {
      title: "7. Cart & Checkout Agents",
      layer: "Layer 4: Commerce Infrastructure",
      desc: "Multi-merchant cart aggregation, dynamic quotes, tax & shipping calculation, and atomic inventory checkout reservations."
    },
    authorization: {
      title: "8. Delegated Authorization Layer",
      layer: "Layer 5: Trust & Bounded Autonomy",
      desc: "Auto-approves within policy (Groceries <= ₹3k, Tech <= ₹10k) while strictly triggering PIN/Biometric approval for high-ticket items (> ₹10k) and blocking hard ceiling violations."
    },
    payment: {
      title: "9. Payment Agent & Sandbox",
      layer: "Layer 5: Zero Raw Card Storage",
      desc: "Scoped authorization tokens dispatched to isolated payment sandbox with automated failover from declined instruments to secondary virtual tokens."
    },
    order: {
      title: "10. Order Agent & Tracking",
      layer: "Layer 4: Post-Purchase Lifecycle",
      desc: "Real-time dispatch tracking, delivery confirmation receipts, automated RMA returns, and cryptographically chained SHA-256 audit ledger logging."
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              13. Target Production Architecture &amp; Supporting Infrastructure
            </h2>
            <p className="text-xs text-slate-400">
              End-to-End System Topology • Next.js UI • FastAPI • LangGraph • Multi-Merchant Gateway • PostgreSQL • Redis • OpenTelemetry • Langfuse
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 bg-black/40 p-1 rounded-xl border border-white/10 text-xs font-mono">
          <button
            onClick={() => setActiveTab('topology')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'topology' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            System Topology
          </button>
          <button
            onClick={() => setActiveTab('infrastructure')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'infrastructure' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Supporting Stack (7)
          </button>
          <button
            onClick={() => setActiveTab('cicd')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'cicd' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            CI/CD &amp; Docker
          </button>
        </div>
      </div>

      {/* TAB 1: SYSTEM TOPOLOGY NODE FLOW */}
      {activeTab === 'topology' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Visual Interactive Architecture Diagram */}
          <div className="lg:col-span-2 glass-panel p-6 border-white/10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Network className="w-4 h-4 text-cyan-400" />
                Target Autonomous System Topology
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">
                Click any component to inspect
              </span>
            </div>

            {/* Architecture Node Map */}
            <div className="space-y-3 font-mono text-xs">
              {/* Node 1: User */}
              <div 
                onClick={() => setSelectedNode('user')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'user' ? 'bg-cyan-950/60 border-cyan-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                  <span>USER ➔ Next.js / React UI</span>
                </div>
                <span className="badge badge-cyan text-[10px]">Layer 1: UX</span>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 2: FastAPI */}
              <div 
                onClick={() => setSelectedNode('gateway')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'gateway' ? 'bg-indigo-950/60 border-indigo-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" />
                  <span>FastAPI API Gateway (REST / MCP / UCP)</span>
                </div>
                <span className="badge badge-indigo text-[10px]">Gateway</span>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 3: LangGraph Supervisor */}
              <div 
                onClick={() => setSelectedNode('supervisor')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'supervisor' ? 'bg-purple-950/60 border-purple-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                  <span>Agent Supervisor (LangGraph State Machine)</span>
                </div>
                <span className="badge badge-purple text-[10px]">Layer 2: Brain</span>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 4: Triad Split */}
              <div className="grid grid-cols-3 gap-2">
                <div 
                  onClick={() => setSelectedNode('intent')}
                  className={`p-2.5 rounded-lg border text-center cursor-pointer transition-all ${
                    selectedNode === 'intent' ? 'bg-pink-950/60 border-pink-400 text-white' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                  }`}
                >
                  <div className="font-bold text-[11px]">Intent Agent</div>
                  <div className="text-[9px] text-slate-400">Spec Extract</div>
                </div>

                <div 
                  onClick={() => setSelectedNode('discovery')}
                  className={`p-2.5 rounded-lg border text-center cursor-pointer transition-all ${
                    selectedNode === 'discovery' ? 'bg-emerald-950/60 border-emerald-400 text-white' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                  }`}
                >
                  <div className="font-bold text-[11px]">Discovery Agent</div>
                  <div className="text-[9px] text-slate-400">M-A, M-B, M-C, M-D</div>
                </div>

                <div 
                  onClick={() => setSelectedNode('authorization')}
                  className={`p-2.5 rounded-lg border text-center cursor-pointer transition-all ${
                    selectedNode === 'authorization' ? 'bg-amber-950/60 border-amber-400 text-white' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                  }`}
                >
                  <div className="font-bold text-[11px]">Policy Engine</div>
                  <div className="text-[9px] text-slate-400">Ceiling &amp; HITL</div>
                </div>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 5: Ranking */}
              <div 
                onClick={() => setSelectedNode('ranking')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'ranking' ? 'bg-purple-950/60 border-purple-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                  <span>Ranking Agent (MCDA + pgvector Memory Fusion)</span>
                </div>
                <span className="badge badge-purple text-[10px]">Evaluation</span>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 6: Cart & Checkout */}
              <div 
                onClick={() => setSelectedNode('cart')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'cart' ? 'bg-cyan-950/60 border-cyan-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                  <span>Cart &amp; Checkout Agents (Multi-Merchant Quotes)</span>
                </div>
                <span className="badge badge-cyan text-[10px]">Infrastructure</span>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 7: Authorization Gate */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-center">
                  <span className="text-emerald-400 font-bold text-[11px]">✓ Auto-Approve</span>
                  <div className="text-[9px] text-slate-400">Groceries ≤₹3k • Tech ≤₹10k</div>
                </div>
                <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-500/30 text-center">
                  <span className="text-amber-400 font-bold text-[11px]">⚠ Human Approval</span>
                  <div className="text-[9px] text-slate-400">Tech &gt; ₹10k (PIN/Biometric)</div>
                </div>
              </div>

              <div className="flex justify-center text-slate-500 font-bold">↓</div>

              {/* Node 8: Payment & Order */}
              <div 
                onClick={() => setSelectedNode('payment')}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedNode === 'payment' ? 'bg-emerald-950/60 border-emerald-400 text-white shadow-lg' : 'bg-black/40 border-white/10 text-slate-300 hover:border-white/30'
                }`}
              >
                <div className="flex items-center gap-2.5 font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span>Payment Agent ➔ Delegated Sandbox ➔ Merchant Order ➔ Tracking</span>
                </div>
                <span className="badge badge-emerald text-[10px]">Settlement</span>
              </div>
            </div>
          </div>

          {/* Right Column: Node Inspector */}
          <div className="glass-panel p-5 space-y-4 border-white/10">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Layers className="w-4 h-4 text-purple-400" />
                Component Inspector
              </h3>
              <span className="badge badge-purple text-[10px]">Active</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 space-y-2">
                <div className="font-bold text-cyan-300 text-sm">
                  {nodeExplanations[selectedNode]?.title}
                </div>
                <div className="text-[10px] text-purple-400 font-bold">
                  {nodeExplanations[selectedNode]?.layer}
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed pt-1">
                  {nodeExplanations[selectedNode]?.desc}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2">
                <div className="font-bold text-slate-400 text-[11px]">Supporting Technologies:</div>
                <div className="flex flex-wrap gap-1.5">
                  <span className="badge badge-indigo text-[10px]">FastAPI</span>
                  <span className="badge badge-purple text-[10px]">LangGraph</span>
                  <span className="badge badge-emerald text-[10px]">PostgreSQL</span>
                  <span className="badge badge-cyan text-[10px]">pgvector</span>
                  <span className="badge badge-amber text-[10px]">Redis</span>
                  <span className="badge badge-rose text-[10px]">OpenTelemetry</span>
                  <span className="badge badge-indigo text-[10px]">Langfuse</span>
                  <span className="badge badge-cyan text-[10px]">Docker</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SUPPORTING INFRASTRUCTURE STACK */}
      {activeTab === 'infrastructure' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {infraData?.services?.map((svc, idx) => (
            <div
              key={idx}
              className="glass-panel p-4 border-white/10 space-y-3 hover:border-cyan-500/40 transition-all font-mono text-xs flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-cyan-400" />
                    <span className="font-bold text-white text-sm">{svc.service_name}</span>
                  </div>
                  <span className="badge badge-emerald text-[10px] py-0 px-2 flex items-center gap-1 font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    {svc.status}
                  </span>
                </div>

                <div className="text-[10px] text-purple-400 font-bold">
                  Role: {svc.role}
                </div>

                <div className="text-[11px] text-slate-400">
                  {svc.details}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-[10px] space-y-1 text-slate-400">
                <div className="truncate text-slate-300">Endpoint: {svc.endpoint}</div>
                <div className="text-emerald-400 font-bold">Latency: {svc.latency_ms} ms</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: CI/CD & DOCKER DEPLOYMENT */}
      {activeTab === 'cicd' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
          <div className="glass-panel p-5 space-y-3 border-white/10">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <span className="font-bold text-white flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-indigo-400" />
                GitHub Actions Pipeline (.github/workflows/ci.yml)
              </span>
              <span className="badge badge-emerald text-[10px]">Automated</span>
            </div>
            <pre className="p-3 rounded-lg bg-black/60 text-slate-300 text-[11px] overflow-x-auto">
{`name: AgentCart CI/CD Pipeline
on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v (57+ Tests Passed)

  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm run build

  docker-build:
    runs-on: ubuntu-latest
    needs: [test-backend, build-frontend]
    steps:
      - run: docker build -t agentcart:latest .`}
            </pre>
          </div>

          <div className="glass-panel p-5 space-y-3 border-white/10">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <span className="font-bold text-white flex items-center gap-2">
                <Box className="w-4 h-4 text-cyan-400" />
                Container Orchestration (docker-compose.yml)
              </span>
              <span className="badge badge-cyan text-[10px]">Compose v3.8</span>
            </div>
            <pre className="p-3 rounded-lg bg-black/60 text-slate-300 text-[11px] overflow-x-auto">
{`version: '3.8'
services:
  agentcart-api:
    build: .
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

  agentcart-ui:
    build: ./frontend
    ports: ["3000:80"]

  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]

  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]

  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports: ["4317:4317"]`}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
