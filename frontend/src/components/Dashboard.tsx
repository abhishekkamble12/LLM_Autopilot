import React from 'react';
import { DollarSign, PiggyBank, Cpu, Database, Activity, ShieldAlert, ArrowUpRight } from 'lucide-react';
import { SystemStats } from '../types';

interface DashboardProps {
  stats: SystemStats;
}

export const Dashboard: React.FC<DashboardProps> = ({ stats }) => {
  const cacheHitRate = stats.totalRequests > 0 
    ? ((stats.cacheHitCount / stats.totalRequests) * 100).toFixed(1)
    : '0.0';

  return (
    <div>
      {/* Top Stat Cards */}
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Total Savings</span>
            <div className="stat-icon" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>
              <PiggyBank className="w-5 h-5" />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>
            +${stats.totalCostSaved.toFixed(4)}
          </div>
          <div className="stat-sub">Compared to baseline Claude 3.5 Sonnet</div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Total Spent</span>
            <div className="stat-icon" style={{ color: 'var(--accent-primary)' }}>
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="stat-value">
            ${stats.totalCostSpent.toFixed(4)}
          </div>
          <div className="stat-sub">Across all routed providers</div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Cache Hit Rate</span>
            <div className="stat-icon" style={{ background: 'var(--info-bg)', color: 'var(--info)' }}>
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--info)' }}>
            {cacheHitRate}%
          </div>
          <div className="stat-sub">{stats.cacheHitCount} lookups served from pgvector</div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Prompts Routed</span>
            <div className="stat-icon" style={{ color: 'var(--accent-secondary)' }}>
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="stat-value">
            {stats.totalRequests}
          </div>
          <div className="stat-sub">Active session queries processed</div>
        </div>
      </div>

      {/* Gateway System Architecture Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginTop: '1rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu className="w-5 h-5 text-indigo-400" />
            <span>ML Router Model Specifications</span>
          </h3>

          <div className="metric-row">
            <span className="label">Complexity Predictor</span>
            <span className="value">Logistic Regression (Balanced)</span>
          </div>
          <div className="metric-row">
            <span className="label">Embedding Engine</span>
            <span className="value">MiniLM-L6-v2 (384 Dimensions)</span>
          </div>
          <div className="metric-row">
            <span className="label">Vector Storage</span>
            <span className="value">PostgreSQL + pgvector extension</span>
          </div>
          <div className="metric-row">
            <span className="label">Shadow Evaluation Rate</span>
            <span className="value">5% Async Background Sampling</span>
          </div>
          <div className="metric-row">
            <span className="label">Telemetry Pipeline</span>
            <span className="value">OpenTelemetry + Prometheus + Grafana</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert className="w-5 h-5 text-purple-400" />
            <span>External Infrastructure Links</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <a
              href="http://localhost:3000"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                padding: '0.875rem 1rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-main)',
                textDecoration: 'none',
                border: '1px solid var(--bg-card-border)',
                transition: 'all 0.2s'
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>Grafana Dashboard</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>http://localhost:3000</div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-indigo-400" />
            </a>

            <a
              href="http://localhost:8000/metrics"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                padding: '0.875rem 1rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-main)',
                textDecoration: 'none',
                border: '1px solid var(--bg-card-border)',
                transition: 'all 0.2s'
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>Prometheus Raw Metrics</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>http://localhost:8000/metrics</div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-indigo-400" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
