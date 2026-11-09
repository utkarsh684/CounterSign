import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatMinorUnits, formatDate } from '../utils/formatters';
import { Plus, FileText, RotateCcw, Sparkles, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { MandateCompileResponse } from '../types';

export default function Mandates() {
  const queryClient = useQueryClient();
  const [showCompiler, setShowCompiler] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [title, setTitle] = useState('');
  const [compiled, setCompiled] = useState<MandateCompileResponse | null>(null);

  const { data: mandates, isLoading } = useQuery({
    queryKey: ['mandates'],
    queryFn: api.listMandates,
  });

  const compileMutation = useMutation({
    mutationFn: (data: { prompt: string; title?: string }) => api.compileMandate(data.prompt, data.title),
    onSuccess: (data) => setCompiled(data),
  });

  const activateMutation = useMutation({
    mutationFn: (data: any) => api.activateMandate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mandates'] });
      setShowCompiler(false);
      setCompiled(null);
      setPrompt('');
      setTitle('');
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => api.revokeMandate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mandates'] }),
  });

  if (isLoading) return <div className="page-spinner"><div className="spinner" /></div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Spending Mandates</h2>
          <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>
            Define financial rules in natural language. AI compiles them into deterministic policies.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCompiler(true)}>
          <Plus size={16} /> New Mandate
        </button>
      </div>

      {/* Compiler Modal */}
      <AnimatePresence>
        {showCompiler && (
          <div className="modal-overlay" onClick={() => setShowCompiler(false)}>
            <motion.div
              className="modal-content"
              style={{ maxWidth: 640 }}
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
            >
              <div className="modal-header">
                <h2><Sparkles size={18} style={{ marginRight: 8, color: 'var(--cs-accent)' }} />Mandate Compiler</h2>
                <button className="btn btn-ghost btn-icon" onClick={() => setShowCompiler(false)}>✕</button>
              </div>
              <div className="modal-body">
                {!compiled ? (
                  <>
                    <div className="form-group" style={{ marginBottom: 16 }}>
                      <label className="form-label">Mandate Title</label>
                      <input
                        className="form-input"
                        placeholder="e.g. Q4 Marketing Budget"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Describe your spending rules in natural language</label>
                      <textarea
                        className="form-textarea"
                        rows={5}
                        placeholder="Allow up to $500 per transaction and $2,000 per week in USD only. Only pay verified vendors on weekdays during business hours. Require human confirmation for anything above $200. Block all new payees."
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                      />
                      <span className="form-hint">Be specific about limits, currencies, timing, and payee rules.</span>
                    </div>
                    <button
                      className="btn btn-primary"
                      style={{ marginTop: 16, width: '100%' }}
                      disabled={!prompt.trim() || compileMutation.isPending}
                      onClick={() => compileMutation.mutate({ prompt, title })}
                    >
                      {compileMutation.isPending ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : <><Sparkles size={14} /> Compile with AI</>}
                    </button>
                    {compileMutation.isError && (
                      <div style={{ marginTop: 12, color: 'var(--cs-danger)', fontSize: 13 }}>
                        {(compileMutation.error as Error).message}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div style={{ marginBottom: 16 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <CheckCircle size={18} style={{ color: 'var(--cs-success)' }} />
                        <span style={{ fontWeight: 600 }}>Mandate Compiled Successfully</span>
                        <span className="badge badge-info">Confidence: {(compiled.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                      <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>{compiled.explanation}</p>
                    </div>

                    {compiled.missing_or_ambiguous_conditions.length > 0 && (
                      <div style={{
                        background: 'var(--cs-warning-light)', border: '1px solid var(--cs-warning-border)',
                        borderRadius: 8, padding: '12px 14px', marginBottom: 16
                      }}>
                        <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--cs-warning)', marginBottom: 6 }}>
                          <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                          Ambiguous or Missing Conditions
                        </div>
                        <ul style={{ fontSize: 13, margin: 0, paddingLeft: 18 }}>
                          {compiled.missing_or_ambiguous_conditions.map((c, i) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )}

                    <div className="card" style={{ marginBottom: 16 }}>
                      <div className="card-header"><h3>Rules Breakdown</h3></div>
                      <div className="card-body" style={{ padding: 0 }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Rule</th>
                              <th>Parameter</th>
                              <th>Value</th>
                              <th>Rationale</th>
                            </tr>
                          </thead>
                          <tbody>
                            {compiled.rules_breakdown.map((rule, i) => (
                              <tr key={i}>
                                <td style={{ fontWeight: 500 }}>{rule.rule}</td>
                                <td className="mono">{rule.parameter}</td>
                                <td className="mono">{rule.value}</td>
                                <td style={{ fontSize: 12, color: 'var(--cs-text-secondary)' }}>{rule.rationale}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        className="btn btn-success"
                        style={{ flex: 1 }}
                        disabled={activateMutation.isPending}
                        onClick={() => activateMutation.mutate({
                          title: title || 'Untitled Mandate',
                          natural_language_prompt: prompt,
                          spec: compiled.spec,
                          explanation: compiled.explanation,
                          rules_breakdown: compiled.rules_breakdown,
                        })}
                      >
                        <CheckCircle size={14} /> Activate Mandate
                      </button>
                      <button className="btn btn-secondary" onClick={() => setCompiled(null)}>
                        <RotateCcw size={14} /> Re-compile
                      </button>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Mandates List */}
      {!mandates?.length ? (
        <div className="card">
          <div className="empty-state">
            <FileText />
            <h3>No mandates yet</h3>
            <p>Create your first spending mandate to define financial rules for your AI agent.</p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Version</th>
                  <th>Per Txn Limit</th>
                  <th>Weekly Limit</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {mandates.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 500 }}>{m.title}</td>
                    <td>
                      <span className={`badge ${m.status === 'ACTIVE' ? 'badge-success' : m.status === 'REVOKED' ? 'badge-danger' : 'badge-neutral'}`}>
                        {m.status}
                      </span>
                    </td>
                    <td>v{m.current_version}</td>
                    <td className="mono">{m.active_version ? formatMinorUnits(m.active_version.per_transaction_limit_minor) : '—'}</td>
                    <td className="mono">{m.active_version ? formatMinorUnits(m.active_version.weekly_limit_minor) : '—'}</td>
                    <td>{formatDate(m.created_at)}</td>
                    <td>
                      {m.status === 'ACTIVE' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => revokeMutation.mutate(m.id)}
                          disabled={revokeMutation.isPending}
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
