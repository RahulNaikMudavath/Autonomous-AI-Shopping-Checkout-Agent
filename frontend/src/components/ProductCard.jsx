import React from 'react';
import { ShoppingCart, Zap, Star, ShieldCheck, Cpu, HardDrive, BatteryCharging, Gauge, Check, Award, Layers, Monitor, Volume2, Wifi } from 'lucide-react';

export default function ProductCard({ 
  product, 
  isTopPick = false, 
  onAddToCart, 
  onInstantBuy, 
  policyThreshold = 50000 
}) {
  if (!product) return null;

  const price = product.price_inr !== undefined ? Number(product.price_inr) : (product.current_price !== undefined ? Number(product.current_price) : 0);
  const requiresApproval = price >= policyThreshold;
  const originalPrice = product.original_price_inr || (product.base_price ? Number(product.base_price) : Math.round(price * 1.15));
  const discountPct = originalPrice > price ? Math.max(5, Math.round(((originalPrice - price) / originalPrice) * 100)) : 0;
  const valueScore = product.value_score || product.mcda_score?.composite_score;

  // Dynamic Specs Extraction
  const renderSpecs = () => {
    const specs = product.specs || {};
    const items = [];

    if (specs.gpu) {
      items.push({ icon: <Cpu className="w-3.5 h-3.5 text-indigo-400 shrink-0" />, label: 'GPU', value: String(specs.gpu).replace('NVIDIA GeForce ', '').split('(')[0] });
    }
    if (specs.ram_gb) {
      items.push({ icon: <Gauge className="w-3.5 h-3.5 text-cyan-400 shrink-0" />, label: 'RAM', value: `${specs.ram_gb}GB` });
    }
    if (specs.ssd_gb) {
      items.push({ icon: <HardDrive className="w-3.5 h-3.5 text-emerald-400 shrink-0" />, label: 'Storage', value: specs.ssd_gb >= 1024 ? `${specs.ssd_gb / 1024}TB` : `${specs.ssd_gb}GB` });
    }
    if (specs.storage_gb) {
      items.push({ icon: <HardDrive className="w-3.5 h-3.5 text-emerald-400 shrink-0" />, label: 'Storage', value: `${specs.storage_gb}GB` });
    }
    if (specs.battery_life_hours || specs.battery_wh) {
      items.push({ icon: <BatteryCharging className="w-3.5 h-3.5 text-amber-400 shrink-0" />, label: 'Battery', value: specs.battery_life_hours ? `${specs.battery_life_hours}h` : `${specs.battery_wh}Wh` });
    }
    if (specs.anc) {
      items.push({ icon: <Volume2 className="w-3.5 h-3.5 text-purple-400 shrink-0" />, label: 'ANC', value: String(specs.anc) });
    }
    if (specs.screen_size || specs.refresh_rate) {
      items.push({ icon: <Monitor className="w-3.5 h-3.5 text-blue-400 shrink-0" />, label: 'Display', value: `${specs.screen_size || ''} ${specs.refresh_rate || ''}`.trim() });
    }
    if (specs.camera_mp) {
      items.push({ icon: <Layers className="w-3.5 h-3.5 text-pink-400 shrink-0" />, label: 'Camera', value: `${specs.camera_mp}MP` });
    }

    // Fallback if none matched
    if (items.length === 0) {
      const entries = Object.entries(specs).slice(0, 4);
      for (const [k, v] of entries) {
        items.push({
          icon: <Layers className="w-3.5 h-3.5 text-indigo-400 shrink-0" />,
          label: k.replace(/_/g, ' '),
          value: String(v)
        });
      }
    }

    return items.slice(0, 4);
  };

  const specItems = renderSpecs();

  return (
    <div className={`glass-panel glass-panel-hover flex flex-col justify-between overflow-hidden relative border transition-all duration-300 rounded-2xl bg-slate-900/90 ${
      isTopPick ? 'border-indigo-500/70 shadow-[0_0_40px_rgba(99,102,241,0.25)] ring-1 ring-indigo-500/50' : 'border-white/10 hover:border-white/20'
    }`}>
      {/* Top Pick / Badge Ribbon */}
      {(isTopPick || product.badge) && (
        <div className="absolute top-3 right-3 z-10">
          <span className="badge badge-indigo flex items-center gap-1.5 shadow-lg px-3 py-1 font-bold text-[11px] bg-indigo-600 text-white border-indigo-400">
            <Award className="w-3.5 h-3.5 text-yellow-300 fill-yellow-300" />
            {product.badge === 'TOP_PICK' || isTopPick ? 'AI TOP RECOMMENDATION' : product.badge?.replace(/_/g, ' ')}
          </span>
        </div>
      )}

      {/* Header & Merchant */}
      <div className="p-5 pb-3">
        <div className="flex items-center justify-between mb-3">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-300 bg-cyan-950/40 px-2.5 py-1 rounded-full border border-cyan-800/40">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            {product.merchant_name || product.merchant_code || "Verified Retailer"}
          </span>
          <div className="flex items-center gap-1 text-xs text-amber-400 font-semibold">
            <Star className="w-3.5 h-3.5 fill-amber-400" />
            {product.rating || "4.8"} ({product.review_count || "120+"})
          </div>
        </div>

        <h3 className="text-base font-bold text-white leading-snug line-clamp-2 title-font">
          {product.title}
        </h3>
        <p className="text-xs text-slate-400 mt-1 line-clamp-1">{product.description}</p>
      </div>

      {/* Specs Grid */}
      <div className="px-5 py-3 border-y border-white/5 bg-black/25">
        <div className="grid grid-cols-2 gap-2 text-xs">
          {specItems.map((s, idx) => (
            <div key={idx} className="spec-chip flex items-center gap-1.5 bg-white/[0.03] p-1.5 rounded-lg border border-white/5 truncate">
              {s.icon}
              <span className="truncate text-slate-300 text-[11px]"><strong className="text-slate-200 capitalize">{s.label}:</strong> {s.value}</span>
            </div>
          ))}
        </div>

        {/* Verified Justification Reasons */}
        {product.reasons && product.reasons.length > 0 && (
          <div className="mt-3 space-y-1 bg-indigo-950/30 p-2.5 rounded-xl border border-indigo-500/20">
            <div className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Verified Agent Justification:</div>
            {product.reasons.map((r, rIdx) => (
              <div key={rIdx} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                <Check className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
                <span>{r}</span>
              </div>
            ))}
          </div>
        )}

        {/* Value Score Meter */}
        {valueScore && (
          <div className="mt-3 p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center font-bold text-xs text-white shadow-md">
                {typeof valueScore === 'number' ? valueScore.toFixed(1) : valueScore}
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">MCDA Value Score</div>
                <div className="text-[10px] text-slate-400">Multi-criteria optimization index</div>
              </div>
            </div>
            {discountPct > 0 && (
              <div className="text-right text-[11px] text-emerald-400 font-mono font-medium">
                Save {discountPct}% off
              </div>
            )}
          </div>
        )}
      </div>

      {/* Pricing & Actions */}
      <div className="p-5 pt-3">
        <div className="flex items-baseline justify-between mb-4">
          <div>
            <div className="text-2xl font-extrabold text-white font-mono tracking-tight">
              ₹{price ? price.toLocaleString() : "0"}
            </div>
            {originalPrice > price && (
              <div className="text-xs text-slate-400 line-through">
                ₹{originalPrice.toLocaleString()}
              </div>
            )}
          </div>

          <div className="text-right">
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
              requiresApproval ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
            }`}>
              {requiresApproval ? '🛡️ Step-Up Authorization' : '⚡ Auto-Approved'}
            </span>
            <div className="text-[10px] text-slate-400 mt-0.5">Express {product.delivery_days || 2}-Day Delivery</div>
          </div>
        </div>

        {/* Buttons */}
        <div className="grid grid-cols-2 gap-2.5">
          <button 
            onClick={() => onAddToCart(product)}
            className="btn-secondary text-xs py-2.5 rounded-xl flex items-center justify-center gap-1.5 hover:bg-white/10"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            Add to Cart
          </button>
          
          <button 
            onClick={() => onInstantBuy(product)}
            className="btn-primary text-xs py-2.5 rounded-xl flex items-center justify-center gap-1.5 shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50"
          >
            <Zap className="w-3.5 h-3.5" />
            Buy Now
          </button>
        </div>
      </div>
    </div>
  );
}
