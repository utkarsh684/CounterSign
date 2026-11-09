import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatMinorUnits, formatDate } from '../utils/formatters';
import { Plus, Users, ShieldCheck, AlertTriangle, Ban } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

export default function Payees() {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', paypal_email: '', category: 'vendor' });
  const [error, setError] = useState('');

  const { data: payees, isLoading } = useQuery({
    queryKey: ['payees'],
    queryFn: api.listPayees,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createPayee(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payees'] });
      setShowAdd(false);
      setForm({ name: '', paypal_email: '', category: 'vendor' });
    },
    onError: (e: Error) => setError(e.message),
  });

  const blockMutation = useMutation({
    mutationFn: (id: string) => api.blockPayee(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payees'] }),
  });

  if (isLoading) return <div className="page-spinner"><div className="spinner" /></div>;

  const statusIcon = (status: string) => {
    switch (status) {
      case 'VERIFIED': return <ShieldCheck size={14} style={{ color: 'var(--cs-success)' }} />;
      case 'BLOCKED': return <Ban size={14} style={{ color: 'var(--cs-danger)' }} />;
      default: return <AlertTriangle size={14} style={{ color: 'var(--cs-warning)' }} />;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Payee Registry</h2>
          <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>
            Manage approved payment recipients. Email changes are hard-rejected for security.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
          <Plus size={16} /> Add Payee
        </button>
      </div>

      {/* Add Payee Modal */}
      <AnimatePresence>
        {showAdd && (
          <div className="modal-overlay" onClick={() => setShowAdd(false)}>
            <motion.div
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
            >
              <div className="modal-header">
                <h2>Add Payee</h2>
                <button className="btn btn-ghost btn-icon" onClick={() => setShowAdd(false)}>✕</button>
              </div>
              <div className="modal-body">
                {error && (
                  <div style={{ background: 'var(--cs-danger-light)', color: 'var(--cs-danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 16 }}>
                    {error}
                  </div>
                )}
                <div className="form-group" style={{ marginBottom: 16 }}>
                  <label className="form-label">Payee Name</label>
                  <input className="form-input" placeholder="Acme Corp" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="form-group" style={{ marginBottom: 16 }}>
                  <label className="form-label">PayPal Email</label>
                  <input className="form-input" type="email" placeholder="payments@acme.com" value={form.paypal_email} onChange={(e) => setForm({ ...form, paypal_email: e.target.value })} />
                  <span className="form-hint">⚠️ Cannot be changed after creation (security policy).</span>
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select className="form-select" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                    <option value="vendor">Vendor</option>
                    <option value="contractor">Contractor</option>
                    <option value="employee">Employee</option>
                    <option value="partner">Partner</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
                <button
                  className="btn btn-primary"
                  disabled={!form.name || !form.paypal_email || createMutation.isPending}
                  onClick={() => createMutation.mutate(form)}
                >
                  {createMutation.isPending ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : 'Add Payee'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Payees Table */}
      {!payees?.length ? (
        <div className="card">
          <div className="empty-state">
            <Users />
            <h3>No payees registered</h3>
            <p>Add your first payee to start processing payments through Countersign.</p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>PayPal Email</th>
                  <th>Category</th>
                  <th>Verification</th>
                  <th>Trust</th>
                  <th>Total Paid</th>
                  <th>Risk Flags</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {payees.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td className="mono" style={{ fontSize: 12 }}>{p.paypal_email}</td>
                    <td><span className="badge badge-neutral">{p.category}</span></td>
                    <td>
                      <span className={`badge ${p.verification_status === 'VERIFIED' ? 'badge-success' : p.verification_status === 'BLOCKED' ? 'badge-danger' : 'badge-warning'}`}>
                        {statusIcon(p.verification_status)} {p.verification_status}
                      </span>
                    </td>
                    <td><span className={`badge ${p.trust_status === 'TRUSTED' ? 'badge-success' : p.trust_status === 'SUSPICIOUS' ? 'badge-danger' : 'badge-neutral'}`}>{p.trust_status}</span></td>
                    <td className="mono">{formatMinorUnits(p.total_paid_minor)}</td>
                    <td>
                      {p.risk_flags.length > 0 ? (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {p.risk_flags.map((f) => <span key={f} className="badge badge-danger" style={{ fontSize: 10 }}>{f}</span>)}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: 'var(--cs-text-tertiary)' }}>None</span>
                      )}
                    </td>
                    <td>
                      {p.verification_status !== 'BLOCKED' && (
                        <button className="btn btn-danger btn-sm" onClick={() => blockMutation.mutate(p.id)} disabled={blockMutation.isPending}>
                          Block
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
