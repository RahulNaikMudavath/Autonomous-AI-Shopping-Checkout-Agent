import React from 'react';
import { Award, ShieldCheck, Sparkles, Check, ArrowRight } from 'lucide-react';

export default function ComparisonMatrix({ 
  products = [], 
  topProduct = null,
  explanation = "",
  tradeOffAnalysis = "",
  onSelectProduct 
}) {
  if (!products || products.length === 0) return null;

  // Determine top 3 spec keys common across products
  const getDynamicSpecKeys = () => {
    const keys = new Set();
    products.forEach(p => {
      if (p.specs) {
        Object.keys(p.specs).forEach(k => keys.add(k));
      }
    });
    // Priority order
    const priority = ['gpu', 'ram_gb', 'ssd_gb', 'storage_gb', 'battery_life_hours', 'anc', 'screen_size', 'refresh_rate', 'driver'];
    const sorted = [...keys].sort((a, b) => {
      const idxA = priority.indexOf(a);
      const idxB = priority.indexOf(b);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return 0;
    });
    return sorted.slice(0, 4);
  };

  const dynamicKeys = getDynamicSpecKeys();

  const formatSpecValue = (key, val) => {
    if (val === undefined || val === null) return "—";
    if (key === 'ram_gb') return `${val}GB`;
    if (key === 'ssd_gb' || key === 'storage_gb') return val >= 1024 ? `${val / 1024}TB` : `${val}GB`;
    if (key === 'battery_life_hours') return `${val} Hours`;
    if (key === 'battery_wh') return `${val}Wh`;
    if (key === 'gpu') return String(val).replace('NVIDIA GeForce ', '').split('(')[0];
    return String(val);
  };

  return (
    <div className="glass-panel p-6 my-6 border border-white/10 bg-slate-900/80 rounded-2xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 pb-3 border-b border-white/10 gap-2">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            AI Multi-Merchant Comparison Matrix
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            MCDA trade-off scoring normalized across price, specifications, warranty & SLAs
          </p>
        </div>
        <span className="badge badge-cyan text-xs self-start sm:self-auto">
          {products.length} Products Compared
        </span>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-black/30">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.04] text-slate-300 font-semibold">
              <th className="p-3 pl-4">Product Name</th>
              <th className="p-3">Merchant</th>
              <th className="p-3">Price</th>
              {dynamicKeys.map(k => (
                <th key={k} className="p-3 capitalize">{k.replace(/_/g, ' ')}</th>
              ))}
              <th className="p-3 pr-4 text-center">Score</th>
              <th className="p-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {products.map((p, idx) => {
              const isWinner = topProduct && p.id === topProduct.id;

              return (
                <tr 
                  key={p.id || idx}
                  className={`transition-colors ${
                    isWinner 
                      ? 'bg-indigo-950/40 hover:bg-indigo-950/60 font-medium text-white' 
                      : 'hover:bg-white/[0.02] text-slate-300'
                  }`}
                >
                  <td className="p-3 pl-4">
                    <div className="flex items-center gap-2">
                      {isWinner && (
                        <Award className="w-4 h-4 text-yellow-400 fill-yellow-400 shrink-0" />
                      )}
                      <span className={`font-semibold ${isWinner ? 'text-indigo-300' : 'text-slate-200'}`}>
                        {p.title ? p.title.split('(')[0] : "Product"}
                      </span>
                    </div>
                  </td>

                  <td className="p-3">
                    <span className="text-slate-400 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-cyan-400" />
                      {p.merchant_name || "Merchant"}
                    </span>
                  </td>

                  <td className="p-3 font-mono font-bold text-white">
                    ₹{p.price_inr ? p.price_inr.toLocaleString() : "0"}
                  </td>

                  {dynamicKeys.map(k => (
                    <td key={k} className="p-3 text-slate-300 font-mono text-[11px]">
                      {formatSpecValue(k, p.specs?.[k])}
                    </td>
                  ))}

                  <td className="p-3 text-center">
                    <span className={`inline-flex items-center justify-center font-bold px-2 py-0.5 rounded-md text-xs font-mono ${
                      isWinner 
                        ? 'bg-gradient-to-r from-indigo-500 to-cyan-500 text-white shadow-md' 
                        : 'bg-white/10 text-slate-300'
                    }`}>
                      {p.value_score || '8.5'}
                    </span>
                  </td>

                  <td className="p-3 pr-4 text-center">
                    <button
                      onClick={() => onSelectProduct && onSelectProduct(p)}
                      className="px-3 py-1 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-[11px] font-semibold transition-all inline-flex items-center gap-1 shadow-sm"
                    >
                      Buy Now
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* AI Explanation & Trade-Off Callout */}
      {(explanation || tradeOffAnalysis) && (
        <div className="mt-4 p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs leading-relaxed space-y-2">
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
