import {
  ApprovalDecision,
  AuditEvent,
  ChainVerificationResult,
  DashboardStats,
  EvidencePackage,
  Invoice,
  Mandate,
  MandateCompileResponse,
  Payee,
  PaymentRequest,
  ScenarioExecutionResult,
  TokenResponse,
  User,
} from "../types";

const BASE_URL = "/api/v1";

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("countersign_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("countersign_token");
    localStorage.removeItem("countersign_user");
    if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/landing")) {
      window.location.href = "/login";
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || errorData.message || "An error occurred");
  }

  return response.json();
}

export const api = {
  // Auth
  login: (data: any) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  register: (data: any) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getMe: () => request<User>("/auth/me"),
  logout: () => {
    localStorage.removeItem("countersign_token");
    localStorage.removeItem("countersign_user");
  },

  // Dashboard
  getDashboardStats: () => request<DashboardStats>("/dashboard/stats"),

  // Mandates
  compileMandate: (prompt: string, title?: string) =>
    request<MandateCompileResponse>("/mandates/compile", {
      method: "POST",
      body: JSON.stringify({ prompt, title }),
    }),
  activateMandate: (data: any) =>
    request<Mandate>("/mandates", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listMandates: () => request<Mandate[]>("/mandates"),
  revokeMandate: (id: string) =>
    request<Mandate>(`/mandates/${id}/revoke`, {
      method: "POST",
    }),

  // Payees
  listPayees: () => request<Payee[]>("/payees"),
  createPayee: (data: any) =>
    request<Payee>("/payees", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updatePayee: (id: string, data: any) =>
    request<Payee>(`/payees/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  blockPayee: (id: string) =>
    request<Payee>(`/payees/${id}/block`, {
      method: "POST",
    }),

  // Invoices
  listInvoices: () => request<Invoice[]>("/invoices"),
  uploadInvoice: async (file: File): Promise<Invoice> => {
    const formData = new FormData();
    formData.append("file", file);
    const headers = {
      ...getAuthHeader(),
    };
    const response = await fetch(`${BASE_URL}/invoices/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return response.json();
  },

  // Agent
  processInvoiceWithAgent: (invoiceId: string, mode: "LIVE" | "SCRIPTED_COMPROMISED" = "LIVE") =>
    request<any>("/agent/process", {
      method: "POST",
      body: JSON.stringify({ invoice_id: invoiceId, mode }),
    }),
  listScenarios: () => request<ScenarioExecutionResult[]>("/agent/scenarios"),
  runScenario: (scenarioId: string) =>
    request<ScenarioExecutionResult>("/agent/run-scenario", {
      method: "POST",
      body: JSON.stringify({ scenario_id: scenarioId }),
    }),

  // Gateway
  submitPaymentRequest: (data: any) =>
    request<PaymentRequest>("/gateway/payments", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listPaymentRequests: () => request<PaymentRequest[]>("/gateway/payments"),

  // Approvals
  listApprovals: () => request<ApprovalDecision[]>("/approvals"),
  approvePayment: (paymentId: string, data: any) =>
    request<ApprovalDecision>(`/approvals/${paymentId}/approve`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  rejectPayment: (paymentId: string, reason: string) =>
    request<ApprovalDecision>(`/approvals/${paymentId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  // PayPal
  getPayPalStatus: () => request<any>("/paypal/status"),
  testPayPalConnection: () =>
    request<any>("/paypal/test-connection", {
      method: "POST",
    }),
  reconcilePayout: (payoutId: string) =>
    request<any>(`/paypal/payments/${payoutId}/reconcile`, {
      method: "POST",
    }),

  // Audit
  getAuditLedger: () => request<AuditEvent[]>("/audit"),
  verifyChain: () => request<ChainVerificationResult>("/audit/verify"),
  getEvidencePackage: (paymentId: string) => request<EvidencePackage>(`/audit/${paymentId}/evidence`),
  simulateTamper: () =>
    request<any>("/audit/simulate-tamper", {
      method: "POST",
    }),

  // Security
  toggleKillSwitch: (enabled: boolean, reason?: string) =>
    request<any>("/security/kill-switch", {
      method: "POST",
      body: JSON.stringify({ enabled, reason }),
    }),
  getSecurityAlerts: () => request<any[]>("/security/alerts"),
};
