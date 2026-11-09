import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatMinorUnits, formatDate } from '../utils/formatters';
import { Upload, FileSearch, AlertTriangle, CheckCircle, Eye } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Invoice } from '../types';

export default function Invoices() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState<Invoice | null>(null);

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: api.listInvoices,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadInvoice(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  if (isLoading) return <div className="page-spinner"><div className="spinner" /></div>;

  const severityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'badge-danger';
      case 'WARNING': return 'badge-warning';
      default: return 'badge-info';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Invoice Analysis</h2>
          <p style={{ fontSize: 13, color: 'var(--cs-text-secondary)' }}>
            Upload invoices for AI-powered analysis. Detects prompt injection, social engineering, and fraud.
          </p>
        </div>
        <div>
          <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{ display: 'none' }} onChange={handleUpload} />
          <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}>
            {uploadMutation.isPending ? <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : <><Upload size={16} /> Upload Invoice</>}
          </button>
        </div>
      </div>

      {uploadMutation.isError && (
        <div style={{ background: 'var(--cs-danger-light)', color: 'var(--cs-danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 16 }}>
          {(uploadMutation.error as Error).message}
        </div>
      )}

      {/* Invoices Table */}
      {!invoices?.length ? (
        <div className="card">
          <div className="empty-state">
            <FileSearch />
            <h3>No invoices uploaded</h3>
            <p>Upload a PDF or image invoice for AI-powered security analysis and metadata extraction.</p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Findings</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="mono" style={{ fontWeight: 500 }}>{inv.invoice_number}</td>
                    <td>
                      <div>{inv.vendor_name}</div>
                      <div style={{ fontSize: 11, color: 'var(--cs-text-tertiary)' }}>{inv.vendor_email}</div>
                    </td>
                    <td className="mono">{formatMinorUnits(inv.total_amount_minor, inv.currency)}</td>
                    <td>
                      <span className={`badge ${inv.status === 'CLEAN' ? 'badge-success' : inv.status === 'SUSPICIOUS' ? 'badge-danger' : 'badge-warning'}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td>
                      {inv.security_findings.length > 0 ? (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {inv.security_findings.slice(0, 2).map((f, i) => (
                            <span key={i} className={`badge ${severityBadge(f.severity)}`} style={{ fontSize: 10 }}>
                              {f.category}
                            </span>
                          ))}
                          {inv.security_findings.length > 2 && (
                            <span className="badge badge-neutral" style={{ fontSize: 10 }}>+{inv.security_findings.length - 2}</span>
                          )}
                        </div>
                      ) : (
                        <span className="badge badge-success"><CheckCircle size={10} /> Clean</span>
                      )}
                    </td>
                    <td>{formatDate(inv.created_at)}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => setSelected(inv)}>
                        <Eye size={14} /> View
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
              style={{ maxWidth: 640 }}
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
            >
              <div className="modal-header">
                <h2>Invoice Details: {selected.invoice_number}</h2>
                <button className="btn btn-ghost btn-icon" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div className="modal-body">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                  <div><span className="form-label">Vendor</span><div>{selected.vendor_name}</div></div>
                  <div><span className="form-label">Email</span><div className="mono" style={{ fontSize: 12 }}>{selected.vendor_email}</div></div>
                  <div><span className="form-label">Amount</span><div className="mono" style={{ fontWeight: 600, fontSize: 18 }}>{formatMinorUnits(selected.total_amount_minor, selected.currency)}</div></div>
                  <div><span className="form-label">SHA-256</span><div className="mono" style={{ fontSize: 10, wordBreak: 'break-all' }}>{selected.file_sha256}</div></div>
                </div>

                {selected.security_findings.length > 0 && (
                  <div>
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
                      <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 6, color: 'var(--cs-warning)' }} />
                      Security Findings
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {selected.security_findings.map((f, i) => (
                        <div key={i} style={{ border: '1px solid var(--cs-border)', borderRadius: 8, padding: 12 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span className={`badge ${severityBadge(f.severity)}`}>{f.severity}</span>
                            <span style={{ fontWeight: 600, fontSize: 13 }}>{f.title}</span>
                          </div>
                          <p style={{ fontSize: 12, color: 'var(--cs-text-secondary)', margin: 0 }}>{f.description}</p>
                          {f.evidence_snippet && (
                            <pre style={{ marginTop: 8, fontSize: 11, background: '#F9FAFB', padding: 8, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
                              {f.evidence_snippet}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
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
