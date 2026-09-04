import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import { 
  Bot, ShoppingBag, Shield, Network, Package, Sparkles, Sliders, 
  ExternalLink, CheckCircle, Zap, RefreshCw, AlertTriangle, Brain, Puzzle, Store, Cable, CreditCard, ShieldAlert, KeyRound, RotateCcw, Database, Activity, FlaskConical, Building2, Settings, ChevronDown, Layers, ArrowLeft, Laptop, Headphones, Smartphone, Monitor 
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
import MemoryConsole from './components/MemoryConsole';
import AgentObservabilityConsole from './components/AgentObservabilityConsole';
import BenchmarkEvaluationConsole from './components/BenchmarkEvaluationConsole';
import SystemArchitectureMap from './components/SystemArchitectureMap';
import ApiSettingsModal from './components/ApiSettingsModal';

const API_BASE = 'http://localhost:8000';

const FEATURED_CATEGORIES = [
  { 
    title: "AI & ML Dev Laptops", 
    desc: "32GB+ RAM, NVIDIA RTX GPUs, High thermal headroom", 
    icon: <Laptop className="w-5 h-5 text-indigo-400" />,
    query: "I need a laptop for AI/ML development under ₹1.2 lakh with 32GB RAM and RTX GPU."
  },
  { 
    title: "ANC Headphones", 
    desc: "Sony WH-1000XM5, Bose, 30+ hour battery life", 
    icon: <Headphones className="w-5 h-5 text-cyan-400" />,
    query: "Find the best noise cancelling headphones under ₹30,000 with 30+ hour battery life."
  },
  { 
    title: "Flagship 5G Phones", 
    desc: "12GB RAM, Top tier cameras, Snapdragon 8 Gen 3", 
    icon: <Smartphone className="w-5 h-5 text-purple-400" />,
    query: "I need a flagship 5G smartphone with top tier camera and 12GB RAM under ₹1.2 lakh."
  },
  { 
    title: "4K 144Hz Monitors", 
    desc: "IPS panels, 1ms response time, HDR 600+", 
    icon: <Monitor className="w-5 h-5 text-emerald-400" />,
    query: "Find me a 4K 144Hz IPS gaming monitor with 1ms response time under ₹50,000."
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('shopping'); // 'shopping' | 'orders' | 'safety' | 'brain' | 'specialized' | 'merchants' | 'gateway' | 'payments' | 'security' | 'permissions' | 'resiliency' | 'memory' | 'observability' | 'benchmark' | 'architecture' | 'protocols'
  
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
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDevMenuOpen, setIsDevMenuOpen] = useState(false);
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
        // Refresh brain & audit
        fetchInitialData();
      } else {
        const err = await res.json();
        alert(`Search error: ${err.detail || "Failed to process shopping request"}`);
      }
    } catch (err) {
      console.error("Query dispatch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Cart Handlers
  const handleAddToCart = async (product) => {
    try {
      const res = await fetch(`${API_BASE}/api/cart/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product, quantity: 1 })
      });
      if (res.ok) {
        const updatedCart = await res.json();
        setCart(updatedCart);
        triggerToast(`Added ${product.title.split('(')[0]} to Cart`);
        setIsCartOpen(true);
      }
    } catch (err) {
      console.error("Error adding to cart:", err);
    }
  };

  const handleRemoveFromCart = async (productId) => {
    try {
      const res = await fetch(`${API_BASE}/api/cart/items/${productId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        const updatedCart = await res.json();
        setCart(updatedCart);
      }
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

  const handleApproveHitl = async (product) => {
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
        
        // Refresh audit logs & cart
        fetchInitialData();

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
        triggerToast("Spending policy updated successfully");
        fetchInitialData();
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
        fetchInitialData();
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

  const isDevTab = activeTab !== 'shopping' && activeTab !== 'orders' && activeTab !== 'safety';

  return (
    <div className="min-h-screen flex flex-col text-slate-100 pb-16 bg-[#090d16]">
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 text-xs font-semibold animate-in fade-in slide-in-from-top-4 duration-300">
          <CheckCircle className="w-4 h-4 text-emerald-300" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Top Navigation Bar: Minimal & Uncluttered */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/85 backdrop-blur-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('shopping')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-[0_0_20px_rgba(99,102,241,0.5)]">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-extrabold tracking-tight brand-font bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  AgentCart
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Live Commerce
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono hidden sm:block">
                Autonomous AI Shopping &amp; Checkout
              </div>
            </div>
          </div>

          {/* Center Navigation: Essential Consumer Tabs */}
          <nav className="flex items-center gap-1.5 bg-white/[0.03] p-1 rounded-xl border border-white/10 text-xs font-medium">
            <button
              onClick={() => setActiveTab('shopping')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'shopping' 
                  ? 'bg-indigo-600 text-white shadow-md font-bold' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Shop &amp; Copilot</span>
            </button>

            <button
              onClick={() => setActiveTab('orders')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'orders' 
                  ? 'bg-indigo-600 text-white shadow-md font-bold' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Package className="w-3.5 h-3.5 text-emerald-400" />
              <span>Orders ({orders.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('safety')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all ${
                activeTab === 'safety' 
                  ? 'bg-indigo-600 text-white shadow-md font-bold' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-purple-400" />
              <span>Spending Policy</span>
            </button>
          </nav>

          {/* Top Right Actions */}
          <div className="flex items-center gap-2">
            {/* API Keys */}
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="btn-secondary py-1.5 px-3 rounded-lg flex items-center gap-1.5 text-xs text-slate-300 hover:text-white"
              title="Configure API Keys"
            >
              <Settings className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden md:inline">API Keys</span>
            </button>

            {/* Cart Button */}
            <button
              onClick={() => setIsCartOpen(true)}
              className="relative btn-secondary py-1.5 px-3.5 rounded-lg flex items-center gap-1.5 text-xs text-slate-200"
              title="View Cart"
            >
              <ShoppingBag className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden md:inline">Cart</span>
              {cart?.items?.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-indigo-600 text-white font-bold text-[10px]">
                  {cart.items.length}
                </span>
              )}
            </button>

            {/* Discreet Developer Lab Menu */}
            <div className="relative">
              <button
                onClick={() => setIsDevMenuOpen(!isDevMenuOpen)}
                className={`flex items-center gap-1 py-1.5 px-2.5 rounded-lg text-xs transition-all ${
                  isDevTab
                    ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40 font-bold'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                }`}
                title="Agent Architecture & Diagnostics"
              >
                <Layers className="w-3.5 h-3.5" />
                <span className="hidden lg:inline text-[11px] font-mono">Dev Lab</span>
                <ChevronDown className="w-3 h-3" />
              </button>

              {isDevMenuOpen && (
                <div className="absolute top-full right-0 mt-2 w-64 p-2 rounded-xl bg-slate-950/95 border border-white/10 shadow-2xl backdrop-blur-2xl z-50 grid grid-cols-1 gap-1 text-xs font-mono">
                  <div className="px-2 py-1 text-[10px] uppercase font-bold text-slate-500">Agent Intelligence</div>
                  <button onClick={() => { setActiveTab('brain'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🧠 Brain &amp; LangGraph</button>
                  <button onClick={() => { setActiveTab('specialized'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🧩 Specialized Subagents</button>
                  <button onClick={() => { setActiveTab('memory'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">💾 4-Tier Memory &amp; Vector DB</button>
                  <button onClick={() => { setActiveTab('observability'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">📈 Observability &amp; Waterfall</button>
                  
                  <div className="px-2 py-1 text-[10px] uppercase font-bold text-slate-500 mt-1 border-t border-white/5 pt-1">Trust &amp; Infrastructure</div>
                  <button onClick={() => { setActiveTab('merchants'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🏪 Merchant Simulator</button>
                  <button onClick={() => { setActiveTab('gateway'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🔌 Commerce Gateway</button>
                  <button onClick={() => { setActiveTab('payments'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">💳 Delegated Payments</button>
                  <button onClick={() => { setActiveTab('security'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🛡️ Security &amp; Sanitizer</button>
                  <button onClick={() => { setActiveTab('permissions'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🔐 RBAC Permissions</button>
                  <button onClick={() => { setActiveTab('resiliency'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🔄 Failure Recovery</button>
                  <button onClick={() => { setActiveTab('benchmark'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🧪 Benchmark (TC01-TC12)</button>
                  <button onClick={() => { setActiveTab('architecture'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🏗️ Architecture Topology</button>
                  <button onClick={() => { setActiveTab('protocols'); setIsDevMenuOpen(false); }} className="p-2 text-left hover:bg-white/5 rounded-lg text-slate-200 flex items-center gap-2">🌐 UCP &amp; MCP Protocols</button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 flex-1 w-full">
        {/* Back Button if in Dev Tab */}
        {isDevTab && (
          <div className="mb-4">
            <button
              onClick={() => setActiveTab('shopping')}
              className="inline-flex items-center gap-2 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors bg-white/[0.03] px-3 py-1.5 rounded-lg border border-white/5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Shopping</span>
            </button>
          </div>
        )}

        {/* TAB 1: SHOPPING COPILOT */}
        {activeTab === 'shopping' && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Hero Search Interface */}
            <ChatInterface 
              onSubmitQuery={handleSearchQuery}
              isLoading={isLoading}
            />

            {/* Agent Live Reasoning Trace (Collapsible) */}
            {recommendation?.trace && (
              <AgentTraceTimeline trace={recommendation.trace} />
            )}

            {/* When No Search Has Occurred: Clean Featured Showcase */}
            {!recommendation && !isLoading && (
              <div className="pt-4 space-y-4 max-w-4xl mx-auto">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">
                    Featured Autonomous Categories
                  </h2>
                  <span className="text-xs text-slate-500">Live multi-merchant search</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {FEATURED_CATEGORIES.map((cat, idx) => (
                    <div 
                      key={idx}
                      onClick={() => handleSearchQuery(cat.query)}
                      className="glass-panel p-4 border-white/10 hover:border-indigo-500/40 cursor-pointer transition-all duration-200 hover:scale-[1.01] rounded-2xl bg-slate-900/60 group"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2.5 rounded-xl bg-white/[0.04] border border-white/5 group-hover:bg-indigo-600/20 group-hover:border-indigo-500/30 transition-all">
                          {cat.icon}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                            {cat.title}
                          </h3>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {cat.desc}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Product Recommendations & Ranking */}
            {recommendation?.comparison_table && recommendation.comparison_table.length > 0 && (
              <div className="space-y-6 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    Autonomous Product Evaluation &amp; Ranking
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">
                    {recommendation.comparison_table.length} verified candidate products
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
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

                {/* Side-by-Side Comparison Matrix */}
                <ComparisonMatrix 
                  products={recommendation.comparison_table}
                  topProduct={recommendation.top_recommendation}
                  explanation={recommendation.explanation}
                  tradeOffAnalysis={recommendation.trade_off_analysis}
                  onSelectProduct={(p) => handleInstantBuy(p)}
                />
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MY ORDERS */}
        {activeTab === 'orders' && (
          <OrdersTracker 
            orders={orders}
            onReturnOrder={handleReturnOrder}
          />
        )}

        {/* TAB 3: SPENDING POLICY */}
        {activeTab === 'safety' && (
          <SafetyDashboard 
            policy={policy}
            onUpdatePolicy={handleUpdatePolicy}
            auditLedger={auditLedger}
            onRefreshLedger={fetchInitialData}
            onVerifyLedger={handleVerifyLedger}
          />
        )}

        {/* DEV LAB TABS */}
        {activeTab === 'brain' && <AgentBrainMap activeStage={brainState?.session?.active_stage || "IDLE"} />}
        {activeTab === 'specialized' && <SpecializedAgentsConsole />}
        {activeTab === 'merchants' && <MerchantSimulatorExplorer />}
        {activeTab === 'gateway' && <CommerceGatewayExplorer />}
        {activeTab === 'payments' && <DelegatedPaymentSandbox />}
        {activeTab === 'security' && <AgentSecurityCenter />}
        {activeTab === 'permissions' && <ToolPermissionsMatrix />}
        {activeTab === 'resiliency' && <FailureRecoveryCenter />}
        {activeTab === 'memory' && <MemoryConsole />}
        {activeTab === 'observability' && <AgentObservabilityConsole />}
        {activeTab === 'benchmark' && <BenchmarkEvaluationConsole />}
        {activeTab === 'architecture' && <SystemArchitectureMap />}
        {activeTab === 'protocols' && <ProtocolExplorer />}
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

      {/* Real API Keys & Integrations Modal */}
      <ApiSettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaveSuccess={(msg) => triggerToast(msg)}
      />
    </div>
  );
}
