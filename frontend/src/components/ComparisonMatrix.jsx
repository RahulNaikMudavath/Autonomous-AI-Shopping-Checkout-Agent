import React from 'react';
import { Table, CheckCircle, Award, ArrowUpRight, ShieldCheck, Sparkles } from 'lucide-react';

export default function ComparisonMatrix({ 
  products = [], 
  topProduct = null,
  explanation = "",
  tradeOffAnalysis = "",
  onSelectProduct 
}) {
  if (!products || products.length === 0) return null;

  return (
    <div className="glass-panel p-6 my-6 border border-white/10 bg-slate-900/80">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Autonomous Multi-Merchant Comparison Matrix
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized across specs, thermal performance, and budget efficiency
          </p>
        </div>
        <span className="badge badge-cyan text-xs">
          {products.length} Models Evaluated
        </span>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto rounded-lg border border-white/10 bg-black/30">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.04] text-slate-300 font-semibold">
              <th className="p-3 pl-4">Product</th>
              <th className="p-3">Merchant</th>
              <th className="p-3">Price</th>
              <th className="p-3">GPU</th>
              <th className="p-3">RAM</th>
              <th className="p-3">SSD</th>
              <th className="p-3">Battery</th>
              <th className="p-3 pr-4 text-center">Value Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {products.map((p, idx) => {
              const isWinner = topProduct && p.id === topProduct.id;

              return (
                <tr 
                  key={p.id || idx}
                  className={`transition-colors cursor-pointer ${
                    isWinner 
                      ? 'bg-indigo-950/40 hover:bg-indigo-950/60 font-medium text-white' 
                      : 'hover:bg-white/[0.02] text-slate-300'
                  }`}
                  onClick={() => onSelectProduct && onSelectProduct(p)}
                >
                  <td className="p-3 pl-4">
                    <div className="flex items-center gap-2">
                      {isWinner && (
                        <Award className="w-4 h-4 text-yellow-400 fill-yellow-400 shrink-0" />
                      )}
                      <span className={`font-semibold ${isWinner ? 'text-indigo-300' : 'text-slate-200'}`}>
                        {p.title.split('(')[0]}
                      </span>
                    </div>
                  </td>

                  <td className="p-3">
                    <span className="text-slate-400 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-cyan-400" />
                      {p.merchant_name}
                    </span>
                  </td>

                  <td className="p-3 font-mono font-bold text-white">
                    ₹{p.price_inr.toLocaleString()}
                  </td>

                  <td className="p-3">
                    <span className="badge badge-indigo text-[11px] py-0.5 px-2">
                      {p.specs.gpu.replace('NVIDIA GeForce ', '').split('(')[0]}
                    </span>
                  </td>

                  <td className="p-3 font-mono">
                    {p.specs.ram_gb}GB
                  </td>

                  <td className="p-3 font-mono">
                    {p.specs.ssd_gb >= 1024 ? `${p.specs.ssd_gb / 1024}TB` : `${p.specs.ssd_gb}GB`}
                  </td>

                  <td className="p-3 text-slate-300">
                    {p.specs.battery_wh}Wh ({p.specs.battery_life_hours}h)
                  </td>

                  <td className="p-3 pr-4 text-center">
                    <span className={`inline-flex items-center justify-center font-bold px-2.5 py-1 rounded-md text-xs font-mono ${
                      isWinner 
                        ? 'bg-gradient-to-r from-indigo-500 to-cyan-500 text-white shadow-md' 
                        : 'bg-white/10 text-slate-300'
                    }`}>
                      {p.value_score || '8.5'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* AI Explanation & Trade-Off Callout */}
      {(explanation || tradeOffAnalysis) && (
        <div className="mt-4 p-4 rounded-lg bg-indigo-950/30 border border-indigo-500/30 text-xs leading-relaxed space-y-2">
          {explanation && (
            <div className="text-slate-200">
              <span className="font-bold text-indigo-300">🧠 Agent Decision: </span>
              {explanation}
            </div>
          )}
          {tradeOffAnalysis && (
            <div className="text-slate-300 pt-2 border-t border-indigo-500/20 whitespace-pre-line font-mono text-[11px]">
              {tradeOffAnalysis}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
