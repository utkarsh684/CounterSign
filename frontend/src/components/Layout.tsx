import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  FileText,
  Users,
  FileSearch,
  ShieldCheck,
  CheckCircle,
  BookOpen,
  Swords,
  CreditCard,
  Lock,
  LogOut,
  AlertTriangle,
  Shield,
} from 'lucide-react';

const navItems = [
  { section: 'Overview', items: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  ]},
  { section: 'Operations', items: [
    { to: '/mandates', icon: FileText, label: 'Mandates' },
    { to: '/payees', icon: Users, label: 'Payees' },
    { to: '/invoices', icon: FileSearch, label: 'Invoices' },
    { to: '/gateway', icon: ShieldCheck, label: 'Payment Gateway' },
    { to: '/approvals', icon: CheckCircle, label: 'Approvals', badge: true },
  ]},
  { section: 'Security', items: [
    { to: '/audit', icon: BookOpen, label: 'Audit Ledger' },
    { to: '/red-team', icon: Swords, label: 'Injection Lab' },
    { to: '/security', icon: Lock, label: 'Security Panel' },
  ]},
  { section: 'Integrations', items: [
    { to: '/paypal', icon: CreditCard, label: 'PayPal Sandbox' },
  ]},
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/health');
      return res.json();
    },
    refetchInterval: 15_000,
  });

  const killSwitchActive = health?.kill_switch_active ?? false;

  const pageTitle = (() => {
    const match = navItems.flatMap(s => s.items).find(i => location.pathname.startsWith(i.to));
    return match?.label || 'Countersign';
  })();

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-name">
            <div className="brand-icon">
              <Shield size={17} />
            </div>
            Countersign
          </div>
          <div className="sidebar-tagline">Trust Layer for AI Payments</div>
        </div>

        {navItems.map((section) => (
          <div key={section.section} className="sidebar-section">
            <div className="sidebar-section-label">{section.section}</div>
            <nav className="sidebar-nav">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                >
                  <item.icon size={18} />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}

        <div className="sidebar-footer">
          <div className="env-badge sandbox">
            <span className="dot"></span>
            SANDBOX
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: '#98A2B3' }}>
            {user?.full_name || user?.email}
          </div>
          <button
            className="sidebar-link"
            onClick={logout}
            style={{ marginTop: 8, color: '#EF4444' }}
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="main-content">
        {killSwitchActive && (
          <div className="kill-switch-banner">
            <AlertTriangle size={16} />
            KILL SWITCH ACTIVE — All payment processing is halted
          </div>
        )}
        <div className="top-bar">
          <h1 className="top-bar-title">{pageTitle}</h1>
          <div className="top-bar-actions">
            {health && (
              <span className={`badge ${health.paypal_configured ? 'badge-success' : 'badge-warning'}`}>
                PayPal: {health.paypal_configured ? 'Connected' : 'Not Configured'}
              </span>
            )}
            <span className="badge badge-info">
              AI: {health?.ai_provider || 'loading...'}
            </span>
          </div>
        </div>

        <div className="page-content page-enter">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
