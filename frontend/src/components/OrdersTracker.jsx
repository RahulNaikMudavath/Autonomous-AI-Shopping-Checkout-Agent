import React, { useState } from 'react';
import { 
  Package, Truck, CheckCircle2, RotateCcw, Clock, MapPin, 
  ExternalLink, Hash, ShieldCheck, AlertCircle 
} from 'lucide-react';

export default function OrdersTracker({ orders = [], onReturnOrder }) {
  const [returnOrderId, setReturnOrderId] = useState(null);
  const [returnReason, setReturnReason] = useState("Upgrading to 64GB RAM configuration");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CONFIRMED':
        return <span className="badge badge-indigo">✓ Confirmed</span>;
      case 'PROCESSING':
        return <span className="badge badge-cyan">⚡ Processing</span>;
      case 'SHIPPED':
        return <span className="badge badge-amber">🚚 In Transit</span>;
      case 'DELIVERED':
        return <span className="badge badge-emerald">✨ Delivered</span>;
      case 'RETURN_REQUESTED':
        return <span className="badge badge-rose">🔄 Return Requested</span>;
      default:
        return <span className="badge badge-indigo">{status}</span>;
    }
  };

  const handleConfirmReturn = async () => {
    if (!returnOrderId) return;
    setIsSubmitting(true);
    await onReturnOrder(returnOrderId, returnReason);
    setIsSubmitting(false);
    setReturnOrderId(null);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Package className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              Orders &amp; Returns Lifecycle Console
            </h2>
            <p className="text-xs text-slate-400">
              Layer 4: Real-time autonomous order tracking, carrier dispatch &amp; returns
            </p>
          </div>
        </div>

        <span className="badge badge-indigo text-xs">
          {orders.length} Active Orders
        </span>
      </div>

      {/* Orders List */}
      {orders.length === 0 ? (
        <div className="glass-panel p-12 text-center border-white/10 space-y-3">
          <Package className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-300">No Orders Placed Yet</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Use the Shopping Assistant to find and autonomously checkout your AI workstation or tech gear.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => {
            const isReturnRequested = order.order_status === 'RETURN_REQUESTED';

            return (
              <div 
                key={order.order_id} 
                className="glass-panel p-6 border-white/10 space-y-4 relative overflow-hidden"
              >
                {/* Top Info Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/10 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-white text-sm">
                      {order.order_id}
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="text-cyan-400 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      {order.merchant_name}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-slate-400 font-mono">
                      {new Date(order.created_at).toLocaleDateString()}
                    </span>
                    {getStatusBadge(order.order_status)}
                  </div>
                </div>

                {/* Main Product Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                  <div className="md:col-span-2 space-y-1">
                    <h4 className="text-base font-bold text-white">
                      {order.product.title}
                    </h4>
                    <p className="text-xs text-slate-400">
                      {order.product.specs.gpu} • {order.product.specs.ram_gb}GB RAM • {order.product.specs.ssd_gb}GB SSD
                    </p>
                    <div className="flex items-center gap-2 text-xs text-slate-400 pt-1">
                      <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span className="truncate">{order.shipping_address}</span>
                    </div>
                  </div>

                  <div className="text-right space-y-1">
                    <div className="text-xl font-mono font-extrabold text-white">
                      ₹{order.amount_inr.toLocaleString()}
                    </div>
                    <div className="text-[11px] text-emerald-400 font-mono">
                      Paid via {order.payment_method}
                    </div>
                  </div>
                </div>

                {/* Tracking Stepper */}
                <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-300">
                    <span className="flex items-center gap-1.5 font-semibold">
                      <Truck className="w-4 h-4 text-cyan-400" />
                      Carrier Tracking: <span className="font-mono text-cyan-300">{order.tracking_id}</span>
                    </span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      ETA: {order.estimated_delivery}
                    </span>
                  </div>

                  {/* Status Steps */}
                  <div className="grid grid-cols-4 gap-2 pt-2 text-center text-[10px] font-semibold">
                    <div className="p-2 rounded bg-indigo-950/60 border border-indigo-500/40 text-indigo-200">
                      1. Confirmed
                    </div>
                    <div className="p-2 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-200">
                      2. Dispatched
                    </div>
                    <div className="p-2 rounded bg-amber-950/60 border border-amber-500/40 text-amber-200">
                      3. Out for Delivery
                    </div>
                    <div className="p-2 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-200">
                      4. Delivered
                    </div>
                  </div>
                </div>

                {/* Audit Block Reference & Return Action */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 text-xs">
                  <div className="text-slate-500 font-mono text-[11px] flex items-center gap-1 truncate">
                    <Hash className="w-3 h-3 text-indigo-400" />
                    <span>Audit Block: {order.audit_block_hash ? `${order.audit_block_hash.slice(0, 16)}...` : '00000000...'}</span>
                  </div>

                  <div>
                    {!isReturnRequested ? (
                      <button 
                        onClick={() => setReturnOrderId(order.order_id)}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 text-rose-300 hover:text-rose-200"
                      >
                        <RotateCcw className="w-3.5 h-3.5 text-rose-400" />
                        Initiate Return / Refund
                      </button>
                    ) : (
                      <span className="text-rose-400 font-mono text-xs flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Return in progress: "{order.return_reason}"
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Return Request Modal */}
      {returnOrderId && (
        <div className="modal-overlay">
          <div className="glass-panel max-w-md w-full p-6 border-rose-500/40 shadow-xl space-y-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-3 pb-3 border-b border-white/10">
              <div className="w-10 h-10 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400">
                <RotateCcw className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white font-heading">
                  Request Return &amp; Refund
                </h3>
                <p className="text-xs text-slate-400 font-mono">{returnOrderId}</p>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <label className="block font-semibold text-slate-300">
                Select Reason for Return:
              </label>
              <select 
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                className="form-input text-xs"
              >
                <option value="Upgrading to 64GB RAM configuration">Upgrading to 64GB RAM configuration</option>
                <option value="Found lower price on another merchant">Found lower price on another merchant</option>
                <option value="Performance specs mismatch">Performance specs mismatch</option>
                <option value="No longer required">No longer required</option>
              </select>
              <p className="text-[11px] text-slate-400 mt-1">
                Merchant will arrange pickup within 24-48 hours. Refund will be credited to tokenized payment source.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-3">
              <button 
                onClick={() => setReturnOrderId(null)}
                className="btn-secondary text-xs py-2.5 justify-center"
              >
                Cancel
              </button>
              <button 
                onClick={handleConfirmReturn}
                disabled={isSubmitting}
                className="btn-primary bg-rose-600 hover:bg-rose-500 text-xs py-2.5 justify-center"
              >
                {isSubmitting ? "Processing..." : "Confirm Return"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
