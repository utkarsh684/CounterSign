import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatMinorUnits, formatDate } from '../utils/formatters';
import { ShieldCheck, Eye, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { PaymentRequest } from '../types';

export default function Gateway() {
  const [selected, setSelected] = useState<PaymentRequest | null>(null);
  const [tab, setTab] = useState<'all' | 'approved' | 'denied' | 'escalated'>('all');

  const { data: payments, isLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: api.listPaymentRequests,
    refetchInterval: 5_000,
  });

  if (isLoading) return <div className="page-spinner"><div className="spinner" /></div>;

  const filtered = payments?.filter((p) => {
    if (tab === 'all') return true;
    if (tab === 'approved') return p.overall_decision === 'READY_FOR_APPROVAL';
    if (tab === 'denied') return p.overall_decision === 'DENY';
    if (tab === 'escalated') return p.overall_decision === 'ESCALATE';
    return true;
  }) || [];

  const decisionBadge = (decision: string) => {
    switch (decision) {
      case 'READY_FOR_APPROVAL': return 'badge-success';
      case 'ESCALATE': return 'badge-warning';
      case 'DENY': return 'badge-danger';
      default: return 'badge-neutral';
    }
  };

  const decisionIcon = (decision: string) => {
    switch (decision) {
      case 'READY_FOR_APPROVAL': return <CheckCircle size={12} />;
      case 'ESCALATE': return <AlertTriangle size={12} />;
      case 'DENY': return <XCircle size={12} />;
      default: return null;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Payment Gateway</h2>
        <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>
          All payment requests processed through the deterministic policy engine and AI security verifier.
        </p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(['all', 'approved', 'denied', 'escalated'] as const).map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'all' ? 'All Requests' : t.charAt(0).toUpperCase() + t.slice(1)}
            {payments && (
              <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.7 }}>
                ({t === 'all' ? payments.length : payments.filter(p =>
                  t === 'approved' ? p.overall_decision === 'READY_FOR_APPROVAL' :
                  t === 'denied' ? p.overall_decision === 'DENY' :
                  p.overall_decision === 'ESCALATE'
                ).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Payments Table */}
      {!filtered.length ? (
        <div className="card">
          <div className="empty-state">
            <ShieldCheck />
            <h3>No payment requests</h3>
            <p>Payment requests from your AI agent will appear here after passing through the security pipeline.</p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Recipient</th>
                  <th>Amount</th>
                  <th>Agent</th>
                  <th>Decision</th>
                  <th>Status</th>
                  <th>Attack?</th>
                  <th>Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => (
                  <tr key={p.id}>
                    <td className="mono" style={{ fontSize: 11 }}>{p.id.slice(0, 8)}…</td>
                    <td className="mono" style={{ fontSize: 12 }}>{p.recipient_email}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{formatMinorUnits(p.amount_minor, p.currency)}</td>
                    <td><span className="badge badge-neutral">{p.agent_mode}</span></td>
                    <td>
                      <span className={`badge ${decisionBadge(p.overall_decision)}`}>
                        {decisionIcon(p.overall_decision)} {p.overall_decision.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td><span className="badge badge-neutral">{p.status}</span></td>
                    <td>
                      {p.is_simulated_attack ? (
                        <span className="badge badge-danger">⚠ Attack</span>
                      ) : (
                        <span className="badge badge-success">Clean</span>
                      )}
                    </td>
                    <td style={{ fontSize: 12 }}>{formatDate(p.created_at)}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => setSelected(p)}>
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      <AnimatePresence>
        {selected && (
          <div className="modal-overlay" onClick={() => setSelected(null)}>
            <motion.div
              className="modal-content"
              style={{ maxWidth: 700 }}
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
            >
              <div className="modal-header">
                <h2>Payment Request Details</h2>
                <button className="btn btn-ghost btn-icon" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div className="modal-body">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                  <div><span className="form-label">Recipient</span><div className="mono">{selected.recipient_email}</div></div>
                  <div><span className="form-label">Amount</span><div className="mono" style={{ fontWeight: 700, fontSize: 20 }}>{formatMinorUnits(selected.amount_minor, selected.currency)}</div></div>
                  <div><span className="form-label">Agent Mode</span><div>{selected.agent_mode}</div></div>
                  <div><span className="form-label">Idempotency Key</span><div className="mono" style={{ fontSize: 10 }}>{selected.idempotency_key}</div></div>
                </div>

                {/* Policy Evaluation */}
                {selected.policy_evaluation && (
                  <div className="evidence-section">
                    <div className="evidence-section-header">
                      <ShieldCheck size={14} /> Policy Engine Result
                      <span className={`badge ${decisionBadge(selected.policy_evaluation.outcome)}`} style={{ marginLeft: 8 }}>
                        {selected.policy_evaluation.outcome}
                      </span>
                    </div>
                    <div className="evidence-section-body" style={{ padding: 0 }}>
                      <table className="data-table">
                        <thead>
                          <tr><th>Rule</th><th>Result</th><th>Reason</th></tr>
                        </thead>
                        <tbody>
                          {selected.policy_evaluation.rule_results.map((r) => (
                            <tr key={r.rule_id}>
                              <td style={{ fontWeight: 500, fontSize: 12 }}>{r.rule_name}</td>
                              <td>
                                <span className={`badge ${r.passed ? 'badge-success' : 'badge-danger'}`}>
                                  {r.decision}
                                </span>
                              </td>
                              <td style={{ fontSize: 12, color: 'var(--cs-text-secondary)' }}>{r.reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* AI Verification */}
                {selected.ai_verification && (
                  <div className="evidence-section">
                    <div className="evidence-section-header">
                      <Eye size={14} /> AI Security Verification
                      <span className={`badge ${selected.ai_verification.injection_detected ? 'badge-danger' : 'badge-success'}`} style={{ marginLeft: 8 }}>
                        {selected.ai_verification.injection_detected ? '⚠ Injection Detected' : '✓ Clean'}
                      </span>
                    </div>
                    <div className="evidence-section-body">
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
                        <div><span className="form-label">Risk Level</span><div className={`badge ${selected.ai_verification.risk_level === 'CRITICAL' ? 'badge-danger' : selected.ai_verification.risk_level === 'HIGH' ? 'badge-danger' : selected.ai_verification.risk_level === 'MEDIUM' ? 'badge-warning' : 'badge-success'}`}>{selected.ai_verification.risk_level}</div></div>
                        <div><span className="form-label">Recommendation</span><div>{selected.ai_verification.recommendation}</div></div>
                        <div><span className="form-label">Latency</span><div>{selected.ai_verification.latency_ms}ms</div></div>
                      </div>
                      <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>{selected.ai_verification.explanation}</p>
                    </div>
                  </div>
                )}

                {/* Decision Reasons */}
                {selected.decision_reasons.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <span className="form-label">Decision Reasons</span>
                    <ul style={{ fontSize: 13, paddingLeft: 18, marginTop: 6 }}>
                      {selected.decision_reasons.map((r, i) => <li key={i} style={{ color: 'var(--cs-text-secondary)' }}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
