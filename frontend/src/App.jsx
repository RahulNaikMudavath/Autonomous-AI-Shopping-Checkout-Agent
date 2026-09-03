import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import { 
  Bot, ShoppingBag, Shield, Network, Package, Sparkles, Sliders, 
  ExternalLink, CheckCircle, Zap, RefreshCw, AlertTriangle, Brain, Puzzle, Store, Cable, CreditCard, ShieldAlert, KeyRound, RotateCcw 
} from 'lucide-react';

import ChatInterface from './components/ChatInterface';
import AgentTraceTimeline from './components/AgentTraceTimeline';
import ProductCard from './components/ProductCard';
import ComparisonMatrix from './components/ComparisonMatrix';
import HumanInTheLoopModal from './components/HumanInTheLoopModal';
import SafetyDashboard from './components/SafetyDashboard';
import ProtocolExplorer from './components/ProtocolExplorer';
import OrdersTracker from './components/OrdersTracker';
import CartDrawer from './components/CartDrawer';
import AgentBrainMap from './components/AgentBrainMap';
import SpecializedAgentsConsole from './components/SpecializedAgentsConsole';
import MerchantSimulatorExplorer from './components/MerchantSimulatorExplorer';
import CommerceGatewayExplorer from './components/CommerceGatewayExplorer';
import DelegatedPaymentSandbox from './components/DelegatedPaymentSandbox';
import AgentSecurityCenter from './components/AgentSecurityCenter';
import ToolPermissionsMatrix from './components/ToolPermissionsMatrix';
import FailureRecoveryCenter from './components/FailureRecoveryCenter';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('shopping'); // 'shopping' | 'brain' | 'specialized' | 'merchants' | 'gateway' | 'payments' | 'security' | 'permissions' | 'resiliency' | 'safety' | 'protocols' | 'orders'
  
  // Data State
  const [recommendation, setRecommendation] = useState(null);
  const [cart, setCart] = useState(null);
  const [orders, setOrders] = useState([]);
  const [policy, setPolicy] = useState(null);
  const [auditLedger, setAuditLedger] = useState([]);
  const [brainState, setBrainState] = useState(null);
  
  // UI State
  const [isLoading, setIsLoading] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isHitlModalOpen, setIsHitlModalOpen] = useState(false);
  const [selectedHitlProduct, setSelectedHitlProduct] = useState(null);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [successToast, setSuccessToast] = useState(null);

  // Initial Data Fetch
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      // 1. Fetch Cart
      const cartRes = await fetch(`${API_BASE}/api/cart`);
      if (cartRes.ok) setCart(await cartRes.json());

      // 2. Fetch Orders
      const ordersRes = await fetch(`${API_BASE}/api/orders`);
      if (ordersRes.ok) setOrders(await ordersRes.json());

      // 3. Fetch Policy
      const policyRes = await fetch(`${API_BASE}/api/policy`);
      if (policyRes.ok) setPolicy(await policyRes.json());

      // 4. Fetch Audit Ledger
      const auditRes = await fetch(`${API_BASE}/api/audit-ledger`);
      if (auditRes.ok) setAuditLedger(await auditRes.json());

      // 5. Fetch Brain State
      const brainRes = await fetch(`${API_BASE}/api/agent-brain/state`);
      if (brainRes.ok) setBrainState(await brainRes.json());

      // Run default query if no recommendation yet
      if (!recommendation) {
        handleSearchQuery("I need a laptop for AI/ML development under ₹1.2 lakh. 32GB RAM minimum. NVIDIA GPU. 1TB SSD. Prefer good battery life. Find the best value.");
      }
    } catch (err) {
      console.error("Error fetching initial state:", err);
    }
  };

  const handleSearchQuery = async (queryText) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, session_id: "session_default" })
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendation(data);
        
        // Refresh brain state
        const brainRes = await fetch(`${API_BASE}/api/agent-brain/state`);
        if (brainRes.ok) setBrainState(await brainRes.json());
      }
    } catch (err) {
      console.error("Search query error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToCart = async (product) => {
    try {
      const res = await fetch(`${API_BASE}/api/cart/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id, quantity: 1 })
      });
      if (res.ok) {
        const updatedCart = await res.json();
        setCart(updatedCart);
        setIsCartOpen(true);
        triggerToast(`Added ${product.title} to cart`);
      }
    } catch (err) {
      console.error("Add to cart error:", err);
    }
  };

  const handleRemoveFromCart = async (productId) => {
    try {
      const res = await fetch(`${API_BASE}/api/cart/item/${productId}`, {
        method: 'DELETE'
      });
      if (res.ok) setCart(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearCart = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/cart`, { method: 'DELETE' });
      if (res.ok) setCart(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  // Instant Buy / Autonomous Checkout Trigger
  const handleInstantBuy = (product) => {
    const threshold = policy?.single_item_approval_threshold_inr || 50000;
    if (product.price_inr >= threshold) {
      // Trigger Human in the Loop approval gate
      setSelectedHitlProduct(product);
      setIsHitlModalOpen(true);
    } else {
      // Auto-approved under threshold
      executeDirectCheckout(product);
    }
  };

  const handleApproveHitl = async (product, pin) => {
    await executeDirectCheckout(product, true);
    setIsHitlModalOpen(false);
  };

  const executeDirectCheckout = async (product, userConfirmed = true) => {
    setIsCheckingOut(true);
    try {
      const res = await fetch(`${API_BASE}/api/checkout/authorize-and-pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          user_confirmed: userConfirmed,
          session_id: "session_default"
        })
      });

      if (res.ok) {
        const newOrder = await res.json();
        setOrders(prev => [newOrder, ...prev]);
        
        // Refresh audit logs
        const auditRes = await fetch(`${API_BASE}/api/audit-ledger`);
        if (auditRes.ok) setAuditLedger(await auditRes.json());

        // Confetti celebration
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });

        triggerToast(`🎉 Order ${newOrder.order_id} Confirmed! Total: ₹${newOrder.amount_inr.toLocaleString()}`);
        setActiveTab('orders');
      } else {
        const err = await res.json();
        alert(`Checkout blocked: ${err.detail}`);
      }
    } catch (err) {
      console.error("Checkout execution error:", err);
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleUpdatePolicy = async (newPolicyData) => {
    try {
      const res = await fetch(`${API_BASE}/api/policy`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPolicyData)
      });
      if (res.ok) {
        const updated = await res.json();
        setPolicy(updated);
        triggerToast("Spending policy & safety boundaries updated");
        // Refresh audit
        const auditRes = await fetch(`${API_BASE}/api/audit-ledger`);
        if (auditRes.ok) setAuditLedger(await auditRes.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleReturnOrder = async (orderId, reason) => {
    try {
      const res = await fetch(`${API_BASE}/api/orders/${orderId}/return`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      });
      if (res.ok) {
        const updated = await res.json();
        setOrders(prev => prev.map(o => o.order_id === orderId ? updated : o));
        triggerToast(`Return request initiated for ${orderId}`);
        // Refresh audit
        const auditRes = await fetch(`${API_BASE}/api/audit-ledger`);
        if (auditRes.ok) setAuditLedger(await auditRes.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleVerifyLedger = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/audit-ledger/verify`);
      return await res.json();
    } catch (err) {
      return { valid: false, message: err.message };
    }
  };

  const triggerToast = (msg) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  return (
    <div className="min-h-screen flex flex-col text-slate-100 pb-16">
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 text-xs font-semibold animate-in fade-in slide-in-from-top-4 duration-300">
          <CheckCircle className="w-4 h-4 text-emerald-300" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 glass-panel border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('shopping')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-[0_0_20px_rgba(99,102,241,0.5)]">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-extrabold tracking-tight brand-font gradient-title">
                  AgentCart
                </span>
                <span className="badge badge-indigo text-[10px] py-0 px-2">v1.8</span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono hidden sm:block">
                Autonomous AI Shopping &amp; Checkout Agent
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/10 text-xs font-medium overflow-x-auto max-w-full">
            <button
              onClick={() => setActiveTab('shopping')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'shopping' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Copilot</span>
            </button>

            <button
              onClick={() => setActiveTab('brain')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'brain' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Brain className="w-3.5 h-3.5 text-purple-400" />
              <span>Brain</span>
            </button>

            <button
              onClick={() => setActiveTab('specialized')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'specialized' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Puzzle className="w-3.5 h-3.5 text-pink-400" />
              <span>Agents</span>
            </button>

            <button
              onClick={() => setActiveTab('merchants')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'merchants' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Store className="w-3.5 h-3.5 text-cyan-400" />
              <span>Simulator</span>
            </button>

            <button
              onClick={() => setActiveTab('gateway')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'gateway' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Cable className="w-3.5 h-3.5 text-indigo-400" />
              <span>Gateway</span>
            </button>

            <button
              onClick={() => setActiveTab('payments')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'payments' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <CreditCard className="w-3.5 h-3.5 text-emerald-400" />
              <span>Payments</span>
            </button>

            <button
              onClick={() => setActiveTab('security')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'security' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Security</span>
            </button>

            <button
              onClick={() => setActiveTab('permissions')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'permissions' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <KeyRound className="w-3.5 h-3.5 text-purple-400" />
              <span>Permissions</span>
            </button>

            <button
              onClick={() => setActiveTab('resiliency')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'resiliency' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
              <span>Resiliency</span>
            </button>

            <button
              onClick={() => setActiveTab('safety')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'safety' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-amber-400" />
              <span>Policies</span>
            </button>

            <button
              onClick={() => setActiveTab('protocols')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'protocols' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Network className="w-3.5 h-3.5 text-cyan-400" />
              <span>Protocols</span>
            </button>

            <button
              onClick={() => setActiveTab('orders')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all shrink-0 ${
                activeTab === 'orders' 
                  ? 'bg-indigo-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Package className="w-3.5 h-3.5 text-emerald-400" />
              <span>Orders ({orders.length})</span>
            </button>
          </nav>

          {/* Cart Trigger */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCartOpen(true)}
              className="relative btn-secondary p-2.5 rounded-xl flex items-center justify-center text-slate-200"
              title="View Cart"
            >
              <ShoppingBag className="w-4 h-4" />
              {cart?.items?.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-indigo-500 text-white font-bold text-[10px] flex items-center justify-center shadow-lg">
                  {cart.items.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 flex-1 w-full">
        {/* TAB 1: SHOPPING COPILOT */}
        {activeTab === 'shopping' && (
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Hero Chat Interface */}
            <ChatInterface 
              onSubmitQuery={handleSearchQuery}
              isLoading={isLoading}
              extractedReqs={recommendation?.requirements_extracted}
            />

            {/* Agent Live Reasoning Trace */}
            {recommendation?.trace && (
              <AgentTraceTimeline trace={recommendation.trace} />
            )}

            {/* Top Pick Highlight & Catalog Cards */}
            {recommendation?.comparison_table && recommendation.comparison_table.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                    Autonomous Product Evaluation &amp; Ranking
                  </h3>
                  <span className="text-xs text-slate-400">
                    Showing top candidates matching your specs
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {recommendation.comparison_table.map((prod, idx) => (
                    <ProductCard
                      key={prod.id || idx}
                      product={prod}
                      isTopPick={recommendation.top_recommendation?.id === prod.id}
                      onAddToCart={handleAddToCart}
                      onInstantBuy={handleInstantBuy}
                      policyThreshold={policy?.single_item_approval_threshold_inr || 50000}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Side-by-Side Comparison Matrix */}
            {recommendation?.comparison_table && (
              <ComparisonMatrix 
                products={recommendation.comparison_table}
                topProduct={recommendation.top_recommendation}
                explanation={recommendation.explanation}
                tradeOffAnalysis={recommendation.trade_off_analysis}
                onSelectProduct={(p) => handleInstantBuy(p)}
              />
            )}
          </div>
        )}

        {/* TAB 2: THE AGENT BRAIN */}
        {activeTab === 'brain' && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <AgentBrainMap activeStage={brainState?.session?.active_stage || "IDLE"} />

            {/* Session Context State Inspector */}
            {brainState && (
              <div className="glass-panel p-6 border-white/10 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-white/10">
                  <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                    <Brain className="w-4 h-4 text-cyan-400" />
                    ContextStore: Active Session State &amp; Working Memory
                  </h3>
                  <span className="badge badge-cyan text-xs font-mono">
                    Session: {brainState.session.session_id}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                    <div className="text-slate-400 font-bold">User Profile &amp; Preferences:</div>
                    <div className="text-slate-200">Name: {brainState.user_profile.name}</div>
                    <div className="text-slate-200">Brand Affinity: {brainState.user_profile.brand_affinity.join(', ')}</div>
                    <div className="text-slate-200">Default Shipping: {brainState.user_profile.default_shipping_address}</div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                    <div className="text-slate-400 font-bold">Supervisor Working Scratchpad:</div>
                    <pre className="text-cyan-300 text-[11px] overflow-x-auto">
                      {JSON.stringify(brainState.session.agent_scratchpad, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SPECIALIZED AGENTS */}
        {activeTab === 'specialized' && (
          <SpecializedAgentsConsole />
        )}

        {/* TAB 4: MERCHANT SIMULATOR */}
        {activeTab === 'merchants' && (
          <MerchantSimulatorExplorer />
        )}

        {/* TAB 5: COMMERCE GATEWAY & CAPABILITIES */}
        {activeTab === 'gateway' && (
          <CommerceGatewayExplorer />
        )}

        {/* TAB 6: PAYMENTS & DELEGATED AUTHORIZATION */}
        {activeTab === 'payments' && (
          <DelegatedPaymentSandbox />
        )}

        {/* TAB 7: AGENT SECURITY & PROMPT INJECTION DEFENSE */}
        {activeTab === 'security' && (
          <AgentSecurityCenter />
        )}

        {/* TAB 8: TOOL PERMISSIONS MATRIX */}
        {activeTab === 'permissions' && (
          <ToolPermissionsMatrix />
        )}

        {/* TAB 9: DISTRIBUTED FAILURE RECOVERY */}
        {activeTab === 'resiliency' && (
          <FailureRecoveryCenter />
        )}

        {/* TAB 10: TRUST & SAFETY */}
        {activeTab === 'safety' && (
          <SafetyDashboard 
            policy={policy}
            onUpdatePolicy={handleUpdatePolicy}
            auditLedger={auditLedger}
            onRefreshLedger={fetchInitialData}
            onVerifyLedger={handleVerifyLedger}
          />
        )}

        {/* TAB 11: PROTOCOLS & MCP */}
        {activeTab === 'protocols' && (
          <ProtocolExplorer />
        )}

        {/* TAB 12: ORDERS & RETURNS */}
        {activeTab === 'orders' && (
          <OrdersTracker 
            orders={orders}
            onReturnOrder={handleReturnOrder}
          />
        )}
      </main>

      {/* Human-in-the-Loop Security Authorization Modal */}
      <HumanInTheLoopModal 
        isOpen={isHitlModalOpen}
        product={selectedHitlProduct}
        policyLimit={policy?.single_item_approval_threshold_inr || 50000}
        onApprove={handleApproveHitl}
        onReject={() => setIsHitlModalOpen(false)}
        isProcessing={isCheckingOut}
      />

      {/* Cart Drawer */}
      <CartDrawer 
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onRemoveItem={handleRemoveFromCart}
        onClearCart={handleClearCart}
        onCheckout={() => {
          if (cart?.items?.[0]) {
            setIsCartOpen(false);
            handleInstantBuy(cart.items[0].product);
          }
        }}
        isProcessing={isCheckingOut}
      />
    </div>
  );
}
