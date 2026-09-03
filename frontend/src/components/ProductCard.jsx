import React from 'react';
import { ShoppingCart, Zap, Star, ShieldCheck, Cpu, HardDrive, BatteryCharging, Gauge, Check, Award } from 'lucide-react';

export default function ProductCard({ 
  product, 
  isTopPick = false, 
  onAddToCart, 
  onInstantBuy, 
  policyThreshold = 50000 
}) {
  if (!product) return null;

  const requiresApproval = product.price_inr >= policyThreshold;
  const discountPct = Math.round(((product.original_price_inr - product.price_inr) / product.original_price_inr) * 100);

  return (
    <div className={`glass-panel glass-panel-hover flex flex-col justify-between overflow-hidden relative border transition-all duration-300 ${
      isTopPick ? 'border-indigo-500/60 shadow-[0_0_35px_rgba(99,102,241,0.25)] ring-1 ring-indigo-500/50' : 'border-white/10'
    }`}>
      {/* Top Pick Ribbon */}
      {isTopPick && (
        <div className="absolute top-3 right-3 z-10">
          <span className="badge badge-indigo flex items-center gap-1.5 shadow-lg px-3 py-1 font-bold text-xs bg-indigo-600/90 text-white border-indigo-400">
            <Award className="w-3.5 h-3.5 text-yellow-300 fill-yellow-300" />
            AI TOP RECOMMENDATION
          </span>
        </div>
      )}

      {/* Header & Merchant */}
      <div className="p-5 pb-3">
        <div className="flex items-center justify-between mb-2.5">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-cyan-300 bg-cyan-950/40 px-2.5 py-1 rounded-full border border-cyan-800/40">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            {product.merchant_name}
          </span>
          <div className="flex items-center gap-1 text-xs text-amber-400 font-semibold">
            <Star className="w-3.5 h-3.5 fill-amber-400" />
            {product.rating} ({product.review_count})
          </div>
        </div>

        <h3 className="text-lg font-bold text-white leading-snug line-clamp-2 title-font">
          {product.title}
        </h3>
        <p className="text-xs text-slate-400 mt-1 line-clamp-1">{product.description}</p>
      </div>

      {/* Specs Grid */}
      <div className="px-5 py-3 border-y border-white/5 bg-black/20">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="spec-chip">
            <Cpu className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="truncate"><strong>GPU:</strong> {product.specs.gpu.replace('NVIDIA GeForce ', '')}</span>
          </div>
          <div className="spec-chip">
            <Gauge className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span><strong>RAM:</strong> {product.specs.ram_gb}GB</span>
          </div>
          <div className="spec-chip">
            <HardDrive className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span><strong>SSD:</strong> {product.specs.ssd_gb >= 1024 ? `${product.specs.ssd_gb / 1024}TB` : `${product.specs.ssd_gb}GB`}</span>
          </div>
          <div className="spec-chip">
            <BatteryCharging className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span><strong>Battery:</strong> {product.specs.battery_wh}Wh ({product.specs.battery_life_hours}h)</span>
          </div>
        </div>

        {/* Value Score Meter */}
        {product.value_score && (
          <div className="mt-3 p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center font-bold text-sm text-white shadow-md">
                {product.value_score}
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">MCDA Value Score</div>
                <div className="text-[10px] text-slate-400">High compute efficiency & headroom</div>
              </div>
            </div>
            <div className="text-right text-[11px] text-emerald-400 font-mono">
              Save ₹{(product.original_price_inr - product.price_inr).toLocaleString()} ({discountPct}% off)
            </div>
          </div>
        )}
      </div>

      {/* Pricing & Actions */}
      <div className="p-5 pt-3">
        <div className="flex items-baseline justify-between mb-4">
          <div>
            <div className="text-2xl font-extrabold text-white font-mono tracking-tight">
              ₹{product.price_inr.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 line-through">
              ₹{product.original_price_inr.toLocaleString()}
            </div>
          </div>

          <div className="text-right">
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
              requiresApproval ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
            }`}>
              {requiresApproval ? '🛡️ Step-Up Authorization' : '⚡ Auto-Approved'}
            </span>
            <div className="text-[10px] text-slate-400 mt-0.5">Express {product.delivery_days}-Day Delivery</div>
          </div>
        </div>

        {/* Buttons */}
        <div className="grid grid-cols-2 gap-2.5">
          <button 
            onClick={() => onAddToCart(product)}
            className="btn-secondary text-xs py-2.5"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            Add to Cart
          </button>
          
          <button 
            onClick={() => onInstantBuy(product)}
            className="btn-primary btn-buy-instant text-xs py-2.5"
          >
            <Zap className="w-3.5 h-3.5" />
            Buy Now
          </button>
        </div>
      </div>
    </div>
  );
}
