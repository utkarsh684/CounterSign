import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatMinorUnits } from '../utils/formatters';
import {
  FileText, CheckCircle, ShieldAlert, Clock,
  TrendingUp, AlertTriangle, CreditCard, Shield,
} from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 10_000,
  });

  if (isLoading) {
    return <div className="page-spinner"><div className="spinner" /></div>;
  }

  if (error || !stats) {
    return (
      <div className="empty-state">
        <AlertTriangle size={48} />
        <h3>Unable to load dashboard</h3>
        <p>{(error as Error)?.message || 'Something went wrong'}</p>
      </div>
    );
  }

  const statCards = [
    {
      icon: FileText, color: 'blue',
      label: 'Active Mandate',
      value: stats.active_mandate_title || 'None',
      sub: stats.active_mandate_title ? `v${stats.active_mandate_version}` : 'Create a mandate to start',
    },
    {
      icon: TrendingUp, color: 'blue',
      label: 'Weekly Utilization',
      value: `${stats.weekly_utilization_percent.toFixed(0)}%`,
      sub: `${formatMinorUnits(stats.weekly_spent_minor)} / ${formatMinorUnits(stats.weekly_limit_minor)}`,
    },
    {
      icon: Clock, color: 'amber',
      label: 'Pending Approvals',
      value: stats.pending_approvals_count.toString(),
      sub: 'Awaiting human review',
    },
    {
      icon: CheckCircle, color: 'green',
      label: 'Confirmed Payouts',
      value: stats.confirmed_payouts_count.toString(),
      sub: `${stats.submitted_payouts_count} submitted total`,
    },
    {
      icon: ShieldAlert, color: 'red',
      label: 'Blocked Attacks',
      value: stats.blocked_attacks_count.toString(),
      sub: 'Injection attempts stopped',
    },
    {
      icon: AlertTriangle, color: 'amber',
      label: 'Escalated',
      value: stats.escalated_requests_count.toString(),
      sub: 'Sent for human review',
    },
    {
      icon: CreditCard, color: stats.paypal_connected ? 'green' : 'amber',
      label: 'PayPal Status',
      value: stats.paypal_connected ? 'Connected' : 'Not Configured',
      sub: stats.environment,
    },
    {
      icon: Shield, color: stats.kill_switch_active ? 'red' : 'green',
      label: 'Kill Switch',
      value: stats.kill_switch_active ? 'ACTIVE' : 'Inactive',
      sub: stats.kill_switch_active ? 'All payments halted' : 'System operating normally',
    },
  ];

  return (
    <div>
      {/* Stats Grid */}
      <div className="stats-grid">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            className="stat-card"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.3 }}
          >
            <div className={`stat-icon ${card.color}`}>
              <card.icon size={20} />
            </div>
            <div className="stat-label">{card.label}</div>
            <div className="stat-value" style={{ fontSize: card.label === 'Active Mandate' ? 18 : undefined }}>
              {card.value}
            </div>
            <div className="stat-sub">{card.sub}</div>
          </motion.div>
        ))}
      </div>

      {/* Weekly Budget Progress */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3>Weekly Budget Utilization</h3>
          <span style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>
            {formatMinorUnits(stats.weekly_spent_minor)} of {formatMinorUnits(stats.weekly_limit_minor)}
          </span>
        </div>
        <div className="card-body">
          <div className="progress-bar">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(stats.weekly_utilization_percent, 100)}%`,
                background: stats.weekly_utilization_percent > 90
                  ? 'linear-gradient(90deg, #EF4444, #DC2626)'
                  : stats.weekly_utilization_percent > 70
                    ? 'linear-gradient(90deg, #F59E0B, #D97706)'
                    : undefined,
              }}
            />
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Recent Alerts */}
        <div className="card">
          <div className="card-header">
            <h3>Recent Security Alerts</h3>
          </div>
          <div className="card-body">
            {stats.recent_alerts.length === 0 ? (
              <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>No recent alerts</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {stats.recent_alerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className={`badge badge-${alert.severity === 'CRITICAL' ? 'danger' : alert.severity === 'WARNING' ? 'warning' : 'info'}`}>
                      {alert.severity}
                    </span>
                    <span style={{ fontSize: 13 }}>{alert.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Audit */}
        <div className="card">
          <div className="card-header">
            <h3>Audit Trail (Latest)</h3>
          </div>
          <div className="card-body">
            {stats.recent_audit_events.length === 0 ? (
              <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>No audit events yet</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {stats.recent_audit_events.slice(0, 6).map((evt) => (
                  <div key={evt.seq} className="chain-block valid">
                    <span style={{ fontWeight: 600, minWidth: 30 }}>#{evt.seq}</span>
                    <span className="badge badge-neutral">{evt.type}</span>
                    <span style={{ flex: 1, fontSize: 12, color: 'var(--cs-text-secondary)' }}>{evt.summary}</span>
                    <span style={{ fontSize: 10, color: 'var(--cs-text-tertiary)' }}>{evt.hash?.slice(0, 8)}…</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
