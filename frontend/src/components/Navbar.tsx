import React from 'react';
import { Rocket, LayoutDashboard, MessageSquare, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  activeTab: 'playground' | 'dashboard';
  setActiveTab: (tab: 'playground' | 'dashboard') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="navbar glass">
      <div className="brand">
        <div className="brand-icon">
          <Rocket className="w-5 h-5 text-white" />
        </div>
        <div>
          <span>LLM Autopilot</span>
          <span style={{ fontSize: '0.7rem', color: 'var(--accent-secondary)', display: 'block', fontWeight: 500, marginTop: '-3px' }}>
            Intelligent Gateway
          </span>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'playground' ? 'active' : ''}`}
          onClick={() => setActiveTab('playground')}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Playground</span>
        </button>

        <button
          className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Metrics Dashboard</span>
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--success)' }}>
        <ShieldCheck className="w-4 h-4" />
        <span>Router Active</span>
      </div>
    </header>
  );
};
