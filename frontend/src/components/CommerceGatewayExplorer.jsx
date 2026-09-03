import React, { useState } from 'react';
import { 
  Network, Play, Layers, CheckCircle2, Shuffle, Server, 
  Cpu, ArrowRight, ShieldCheck, Database, SlidersHorizontal 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const CAPABILITIES = [
  { id: 'discover', label: '1. discover_products()', desc: 'Discovers products across multi-merchant catalogs' },
  { id: 'get_prod', label: '2. get_product()', desc: 'Fetches granular specs & stock status' },
  { id: 'create_cart', label: '3. create_cart()', desc: 'Creates stateful cart with selected items' },
  { id: 'update_cart', label: '4. update_cart()', desc: 'Mutates item quantities & recalculates subtotals' },
  { id: 'checkout', label: '5. checkout()', desc: 'Generates binding quote with dynamic tax & promo discounts' },
  { id: 'auth_pay', label: '6. authorize_payment()', desc: 'Authorizes tokenized payment & issues confirmed order' },
  { id: 'get_order', label: '7. get_order()', desc: 'Queries real-time tracking status & carrier ETA' },
  { id: 'cancel_order', label: '8. cancel_order()', desc: 'Initiates immediate cancellation and refund escrow' },
];

const TRANSPORTS = [
  { id: 'AUTO', label: 'AUTO (Smart Resolve)', desc: 'Gateway determines optimal protocol', badge: 'Auto' },
  { id: 'REST_API', label: 'Merchant REST', desc: 'Direct HTTP REST endpoints', badge: 'REST' },
  { id: 'MCP_TOOL', label: 'MCP Tool Call', desc: 'Model Context Protocol tool execution', badge: 'MCP' },
  { id: 'UCP_PROTOCOL', label: 'UCP v1.0 Envelope', desc: 'Universal Commerce Protocol capability envelope', badge: 'UCP' },
];

export default function CommerceGatewayExplorer() {
  const [selectedCap, setSelectedCap] = useState('discover');
  const [selectedTransport, setSelectedTransport] = useState('AUTO');

  // Parameters
  const [merchantId, setMerchantId] = useState('merchant-a');
  const [productId, setProductId] = useState('prod_laptop_b_rog');
  const [cartId, setCartId] = useState('');
  const [quoteId, setQuoteId] = useState('');
  const [orderId, setOrderId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [maxPrice, setMaxPrice] = useState(120000);
  const [promoCode, setPromoCode] = useState('AI_DEVELOPER_5OFF');

  // Response
  const [responseOutput, setResponseOutput] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleExecute = async () => {
    setIsLoading(true);
    let url = '';
    let method = 'POST';
    let body = {};

    try {
      if (selectedCap === 'discover') {
        url = `${API_BASE}/api/gateway/discover-products`;
        body = { category: 'laptop', max_price: parseFloat(maxPrice) || 120000, transport: selectedTransport };
      } else if (selectedCap === 'get_prod') {
        url = `${API_BASE}/api/gateway/product/${merchantId}/${productId}?transport=${selectedTransport}`;
        method = 'GET';
        body = null;
      } else if (selectedCap === 'create_cart') {
        url = `${API_BASE}/api/gateway/cart/create`;
        body = { merchant_id: merchantId, product_id: productId, quantity: parseInt(quantity) || 1, transport: selectedTransport };
      } else if (selectedCap === 'update_cart') {
        url = `${API_BASE}/api/gateway/cart/update`;
        method = 'PATCH';
        body = { merchant_id: merchantId, cart_id: cartId || 'cart_demo', quantity: parseInt(quantity) || 2, transport: selectedTransport };
      } else if (selectedCap === 'checkout') {
        url = `${API_BASE}/api/gateway/checkout`;
        body = { merchant_id: merchantId, cart_id: cartId || 'cart_demo', promo_code: promoCode, transport: selectedTransport };
      } else if (selectedCap === 'auth_pay') {
        url = `${API_BASE}/api/gateway/payment/authorize`;
        body = { merchant_id: merchantId, quote_id: quoteId || 'quote_demo', auth_token: 'PIN_AUTH_9912', transport: selectedTransport };
      } else if (selectedCap === 'get_order') {
        url = `${API_BASE}/api/gateway/orders/${merchantId}/${orderId || 'ORD_DEMO'}?transport=${selectedTransport}`;
        method = 'GET';
        body = null;
      } else if (selectedCap === 'cancel_order') {
        url = `${API_BASE}/api/gateway/orders/cancel`;
        body = { merchant_id: merchantId, order_id: orderId || 'ORD_DEMO', reason: 'User requested cancellation', transport: selectedTransport };
      }

      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (body) options.body = JSON.stringify(body);

      const res = await fetch(url, options);
      const data = await res.json();
      setResponseOutput(data);

      // Auto populate cascade
      if (data.cart_id) setCartId(data.cart_id);
      if (data.quote_id) setQuoteId(data.quote_id);
      if (data.order_id) setOrderId(data.order_id);
      if (Array.isArray(data) && data.length > 0 && data[0].product_id) {
        setProductId(data[0].product_id);
        setMerchantId(data[0].merchant_id);
      }
    } catch (err) {
      setResponseOutput({ error: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Network className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              5. Unified Commerce Gateway &amp; Capability Model
            </h2>
            <p className="text-xs text-slate-400">
              Protocol-agnostic capability layer bridging AI Agents across REST, MCP, and UCP v1.0
            </p>
          </div>
        </div>

        <span className="badge badge-indigo text-xs py-1 px-3">
          UCP &amp; MCP Interoperability
        </span>
      </div>

      {/* Protocol Adapter Mode Selector */}
      <div className="glass-panel p-5 space-y-3 border-white/10">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Shuffle className="w-4 h-4 text-cyan-400" />
            Select Underlying Protocol Adapter:
          </h3>
          <span className="text-[11px] text-slate-400">
            Agent code remains identical regardless of transport
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {TRANSPORTS.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTransport(t.id)}
              className={`p-3 rounded-xl border text-left transition-all ${
                selectedTransport === t.id
                  ? 'bg-indigo-950/80 border-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.3)] ring-1 ring-indigo-400'
                  : 'bg-white/[0.02] border-white/10 text-slate-400 hover:border-white/20'
              }`}
            >
              <div className="text-xs font-bold text-slate-200 flex items-center justify-between">
                <span>{t.label}</span>
                <span className="badge badge-indigo text-[10px] py-0 px-1.5">{t.badge}</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1">{t.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Execution Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Capability Picker */}
        <div className="glass-panel p-5 space-y-2 border-white/10">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            8 Commerce Capabilities
          </h3>

          {CAPABILITIES.map((cap) => (
            <button
              key={cap.id}
              onClick={() => setSelectedCap(cap.id)}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border flex items-center justify-between ${
                selectedCap === cap.id
                  ? 'bg-purple-950/70 border-purple-500 text-white shadow-sm ring-1 ring-purple-400'
                  : 'bg-white/[0.02] border-white/5 text-slate-400 hover:text-white hover:border-white/15'
              }`}
            >
              <div>
                <div className="font-bold text-slate-200">{cap.label}</div>
                <div className="text-[10px] text-slate-500 font-sans mt-0.5">{cap.desc}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Parameter Form & Live Payload */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span className="font-mono text-xs font-bold text-white">
                CommerceGateway.{selectedCap}() [Transport: {selectedTransport}]
              </span>
            </div>

            <button
              onClick={handleExecute}
              disabled={isLoading}
              className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {isLoading ? "Executing Capability..." : "Invoke Capability"}
            </button>
          </div>

          {/* Dynamic parameter inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-1">Target Merchant:</label>
              <select 
                value={merchantId} 
                onChange={(e) => setMerchantId(e.target.value)}
                className="form-input text-xs font-mono"
              >
                <option value="merchant-a">Merchant A (TechHub India)</option>
                <option value="merchant-b">Merchant B (ElectroBazaar)</option>
                <option value="merchant-c">Merchant C (OmniStore Online)</option>
                <option value="merchant-d">Merchant D (ProHardware Direct)</option>
              </select>
            </div>

            {selectedCap === 'discover' && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Max Budget (INR):</label>
                <input 
                  type="number" 
                  value={maxPrice} 
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedCap === 'get_prod' || selectedCap === 'create_cart') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Product ID / SKU:</label>
                <input 
                  type="text" 
                  value={productId} 
                  onChange={(e) => setProductId(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedCap === 'create_cart' || selectedCap === 'update_cart') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Quantity:</label>
                <input 
                  type="number" 
                  min={1} 
                  value={quantity} 
                  onChange={(e) => setQuantity(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedCap === 'update_cart' || selectedCap === 'checkout') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Cart ID:</label>
                <input 
                  type="text" 
                  value={cartId} 
                  onChange={(e) => setCartId(e.target.value)}
                  placeholder="e.g. cart_gw_merc_123"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {selectedCap === 'checkout' && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Promo Code:</label>
                <input 
                  type="text" 
                  value={promoCode} 
                  onChange={(e) => setPromoCode(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {selectedCap === 'auth_pay' && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Quote ID:</label>
                <input 
                  type="text" 
                  value={quoteId} 
                  onChange={(e) => setQuoteId(e.target.value)}
                  placeholder="e.g. q_gw_merc_123"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedCap === 'get_order' || selectedCap === 'cancel_order') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Order ID:</label>
                <input 
                  type="text" 
                  value={orderId} 
                  onChange={(e) => setOrderId(e.target.value)}
                  placeholder="e.g. ORD_GW_MERC_123"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}
          </div>

          {/* Response Inspector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Standardized Gateway Return Object:
              </span>
              {responseOutput && (
                <span className="badge badge-emerald text-[10px]">
                  Transport: {responseOutput.transport_used || selectedTransport}
                </span>
              )}
            </div>

            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 h-64 overflow-y-auto text-xs font-mono text-emerald-300">
              {responseOutput ? (
                <pre>{JSON.stringify(responseOutput, null, 2)}</pre>
              ) : (
                <div className="text-slate-500 italic mt-24 text-center">
                  Click "Invoke Capability" to run the capability method through the Commerce Gateway.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
