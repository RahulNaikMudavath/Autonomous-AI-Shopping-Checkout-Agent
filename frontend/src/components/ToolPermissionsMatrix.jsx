import React, { useState, useEffect } from 'react';
import { 
  KeyRound, ShieldCheck, ShieldAlert, CheckCircle2, XCircle, 
  Play, Lock, Unlock, AlertTriangle, Terminal, Layers, Cpu 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const MATRIX_DATA = [
  { role: 'Discovery Agent', search: true, cart: false, checkout: false, payment: false, desc: 'Federated catalog search & spec normalization' },
  { role: 'Ranking Agent', search: true, cart: false, checkout: false, payment: false, desc: 'MCDA scoring & Pareto frontier evaluation' },
  { role: 'Cart Agent', search: true, cart: true, checkout: false, payment: false, desc: 'Multi-merchant cart aggregation & item management' },
  { role: 'Checkout Agent', search: true, cart: true, checkout: true, payment: false, desc: 'Dynamic quotes, taxes, and spending policy evaluation' },
  { role: 'Payment Agent', search: false, cart: false, checkout: true, payment: true, desc: 'Delegated token settlement on bank rails' },
  { role: 'Order Agent', search: false, cart: false, checkout: false, payment: false, desc: 'Post-purchase carrier tracking and return requests' },
];

const AVAILABLE_TOOLS = [
  { name: 'search_products', label: 'search_products()', category: 'Search' },
  { name: 'get_product_specs', label: 'get_product_specs()', category: 'Search' },
  { name: 'add_to_cart', label: 'add_to_cart()', category: 'Cart' },
  { name: 'update_cart_quantity', label: 'update_cart_quantity()', category: 'Cart' },
  { name: 'create_checkout_quote', label: 'create_checkout_quote()', category: 'Checkout' },
  { name: 'evaluate_spending_policy', label: 'evaluate_spending_policy()', category: 'Checkout' },
  { name: 'authorize_payment', label: 'authorize_payment()', category: 'Payment' },
  { name: 'execute_sandbox_charge', label: 'execute_sandbox_charge()', category: 'Payment' },
];

export default function ToolPermissionsMatrix() {
  const [selectedAgent, setSelectedAgent] = useState('Discovery Agent');
  const [selectedTool, setSelectedTool] = useState('authorize_payment');
  const [testResult, setTestResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  const handleTestInvocation = async () => {
    setIsChecking(true);
    try {
      const res = await fetch(`${API_BASE}/api/security/permissions/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_role: selectedAgent,
          tool_name: selectedTool
        })
      });

      if (res.ok) {
        setTestResult(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 bg-gradient-to-r from-slate-900 via-purple-950/40 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              8. Tool Permission Matrix (Agent RBAC)
            </h2>
            <p className="text-xs text-slate-400">
              Role-based execution boundaries • Mathematical denial of unauthorized capabilities
            </p>
          </div>
        </div>

        <span className="badge badge-purple text-xs py-1 px-3 flex items-center gap-1.5">
          <Lock className="w-3.5 h-3.5 text-purple-300" />
          Runtime Kernel Interceptor Active
        </span>
      </div>

      {/* The Tool Permission Matrix Table */}
      <div className="glass-panel p-5 space-y-3 border-white/10">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-cyan-400" />
            Agent Tool Permission Matrix
          </h3>
          <span className="text-[11px] text-slate-400 font-mono">
            Granular Capability Isolation
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 font-mono text-[11px]">
                <th className="py-2.5 px-3">Agent Role</th>
                <th className="py-2.5 px-3 text-center">Search</th>
                <th className="py-2.5 px-3 text-center">Cart</th>
                <th className="py-2.5 px-3 text-center">Checkout</th>
                <th className="py-2.5 px-3 text-center">Payment</th>
                <th className="py-2.5 px-3">Operational Scope</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {MATRIX_DATA.map((row) => (
                <tr key={row.role} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-3 font-bold text-white flex items-center gap-2">
                    <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                    {row.role}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {row.search ? (
                      <span className="text-emerald-400 font-bold text-sm">✓</span>
                    ) : (
                      <span className="text-rose-400 font-bold text-sm">✗</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {row.cart ? (
                      <span className="text-emerald-400 font-bold text-sm">✓</span>
                    ) : (
                      <span className="text-rose-400 font-bold text-sm">✗</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {row.checkout ? (
                      <span className="text-emerald-400 font-bold text-sm">✓</span>
                    ) : (
                      <span className="text-rose-400 font-bold text-sm">✗</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    {row.payment ? (
                      <span className="text-emerald-400 font-bold text-sm">✓</span>
                    ) : (
                      <span className="text-rose-400 font-bold text-sm">✗</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-400 text-[11px] font-sans">
                    {row.desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interactive Tool Invocation Tester */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Column */}
        <div className="glass-panel p-5 space-y-4 border-white/10">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Test Runtime Permission Interceptor
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-1">Select Agent Role:</label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="form-input text-xs font-mono"
              >
                {MATRIX_DATA.map((r) => (
                  <option key={r.role} value={r.role}>{r.role}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-1">Target Tool to Invoke:</label>
              <select
                value={selectedTool}
                onChange={(e) => setSelectedTool(e.target.value)}
                className="form-input text-xs font-mono"
              >
                {AVAILABLE_TOOLS.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.label} ({t.category})
                  </option>
                ))}
              </select>
            </div>

            {/* Attack Simulation Preset */}
            <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/30 space-y-1.5 text-[11px]">
              <div className="font-bold text-rose-300 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                Scenario: Confused LLM
              </div>
              <p className="text-slate-400">
                Discovery Agent hijacked by malicious prompt attempting to call <code className="text-rose-300">authorize_payment()</code>
              </p>
              <button
                onClick={() => {
                  setSelectedAgent('Discovery Agent');
                  setSelectedTool('authorize_payment');
                }}
                className="text-[10px] bg-rose-900/50 hover:bg-rose-900 text-rose-200 px-2 py-1 rounded font-mono"
              >
                Set: Discovery Agent ➔ Payment Tool
              </button>
            </div>

            <button
              onClick={handleTestInvocation}
              disabled={isChecking}
              className="w-full btn-primary text-xs py-2.5 flex items-center justify-center gap-1.5 font-bold"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {isChecking ? "Testing Interceptor..." : "Test Tool Invocation"}
            </button>
          </div>
        </div>

        {/* Security Result Display */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              Runtime Authorization Verdict
            </span>
            {testResult && (
              <span className={`badge text-xs font-mono font-bold ${
                testResult.allowed ? 'badge-emerald' : 'badge-rose'
              }`}>
                {testResult.allowed ? 'PERMITTED' : 'ACCESS DENIED'}
              </span>
            )}
          </div>

          {testResult ? (
            <div className="space-y-4 animate-in fade-in duration-200">
              {/* Verdict Banner */}
              <div className={`p-4 rounded-xl border space-y-2 ${
                testResult.allowed 
                  ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200' 
                  : 'bg-rose-950/60 border-rose-500 text-rose-200 shadow-lg'
              }`}>
                <div className="text-sm font-bold flex items-center gap-2">
                  {testResult.allowed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-rose-400" />
                  )}
                  {testResult.message}
                </div>

                {!testResult.allowed && (
                  <div className="p-2.5 rounded bg-black/60 border border-rose-800 text-xs font-mono text-amber-200">
                    💡 Security Guarantee: Even if the LLM gets confused or manipulated by malicious descriptions, <strong>{testResult.agent_role} cannot make payments or execute {testResult.tool_category} tools</strong>.
                  </div>
                )}
              </div>

              {/* Invariant Checklist */}
              <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 space-y-2 text-xs font-mono">
                <div className="text-slate-400 font-bold">Execution Inspection:</div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div>Agent Identity: <span className="text-purple-300">{testResult.agent_role}</span></div>
                  <div>Tool Category: <span className="text-cyan-300">{testResult.tool_category}</span></div>
                  <div>Tool Name: <span className="text-slate-200">{testResult.tool_name}</span></div>
                  <div>Security Breach Prevented: <span className={testResult.security_breach_prevented ? 'text-emerald-400 font-bold' : 'text-slate-500'}>{testResult.security_breach_prevented ? 'YES' : 'NO'}</span></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs italic">
              Select an Agent Role and Tool, then click "Test Tool Invocation" to test the permission guardrail.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
