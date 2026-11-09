export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface MandateSpec {
  currency_allowlist: string[];
  per_transaction_limit_minor: number;
  daily_limit_minor: number;
  weekly_limit_minor: number;
  allowed_weekdays: number[];
  operating_hours_start?: string;
  operating_hours_end?: string;
  allow_existing_payees_only: boolean;
  unknown_payee_action: string;
  third_party_evidence_limit_minor: number;
  human_confirmation_required: boolean;
}

export interface RuleExplanation {
  rule: string;
  parameter: string;
  value: string;
  rationale: string;
}

export interface MandateCompileResponse {
  spec: MandateSpec;
  explanation: string;
  rules_breakdown: RuleExplanation[];
  missing_or_ambiguous_conditions: string[];
  confidence_score: number;
}

export interface MandateVersion {
  id: string;
  version: number;
  currency_allowlist: string[];
  per_transaction_limit_minor: number;
  daily_limit_minor: number;
  weekly_limit_minor: number;
  allowed_weekdays: number[];
  allow_existing_payees_only: boolean;
  unknown_payee_action: string;
  third_party_evidence_limit_minor: number;
  human_confirmation_required: boolean;
  compiler_explanation: string;
  compiler_rules_breakdown: RuleExplanation[];
  hmac_signature: string;
  created_at: string;
}

export interface Mandate {
  id: string;
  title: string;
  natural_language_prompt: string;
  status: 'DRAFT' | 'ACTIVE' | 'REVOKED' | 'EXPIRED';
  current_version: number;
  created_at: string;
  updated_at: string;
  active_version?: MandateVersion;
}

export interface Payee {
  id: string;
  name: string;
  paypal_email: string;
  category: string;
  verification_status: 'UNVERIFIED' | 'VERIFIED' | 'BLOCKED';
  trust_status: 'STANDARD' | 'TRUSTED' | 'SUSPICIOUS';
  total_paid_minor: number;
  last_transaction_at?: string;
  risk_flags: string[];
  created_at: string;
  updated_at: string;
}

export interface InvoiceFinding {
  category: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  description: string;
  evidence_snippet?: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  vendor_name: string;
  vendor_email: string;
  issue_date?: string;
  due_date?: string;
  currency: string;
  total_amount_minor: number;
  tax_amount_minor: number;
  file_sha256: string;
  payment_instructions?: string;
  status: string;
  extracted_metadata: Record<string, any>;
  security_findings: InvoiceFinding[];
  created_at: string;
}

export interface RuleResult {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  decision: 'PASS' | 'ESCALATE' | 'DENY';
  reason: string;
  parameter_checked?: string;
  actual_value?: any;
  allowed_value?: any;
}

export interface PolicyEvaluation {
  outcome: 'READY_FOR_APPROVAL' | 'ESCALATE' | 'DENY';
  rules_evaluated: number;
  rules_passed: number;
  rules_failed: number;
  rule_results: RuleResult[];
  latency_ms: number;
  evaluated_at: string;
}

export interface AIVerification {
  provider: string;
  model: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendation: 'CLEAR' | 'ESCALATE' | 'DENY';
  injection_detected: boolean;
  reason_codes: string[];
  evidence_references: string[];
  explanation: string;
  latency_ms: number;
  created_at: string;
}

export interface PaymentRequest {
  id: string;
  invoice_id?: string;
  payee_id?: string;
  agent_id: string;
  agent_mode: string;
  idempotency_key: string;
  recipient_email: string;
  amount_minor: number;
  currency: string;
  overall_decision: 'READY_FOR_APPROVAL' | 'ESCALATE' | 'DENY';
  decision_reasons: string[];
  status: string;
  is_simulated_attack: boolean;
  created_at: string;
  policy_evaluation?: PolicyEvaluation;
  ai_verification?: AIVerification;
  approval_decision?: any;
}

export interface ApprovalDecision {
  id: string;
  payment_request_id: string;
  user_id: string;
  decision: 'APPROVED' | 'REJECTED';
  confirmed_recipient_email: string;
  confirmed_amount_minor: number;
  confirmed_currency: string;
  is_one_time_exception: boolean;
  exception_reason?: string;
  notes?: string;
  decided_at: string;
  paypal_payout?: PayPalPayout;
}

export interface PayPalPayout {
  id: string;
  sender_batch_id: string;
  paypal_batch_id?: string;
  paypal_payout_item_id?: string;
  recipient_email: string;
  amount_minor: number;
  currency: string;
  batch_status: string;
  item_status: string;
  environment: string;
  submitted_at: string;
  reconciled_at?: string;
}

export interface AuditEvent {
  id: string;
  sequence_number: number;
  event_type: string;
  user_id?: string;
  payment_request_id?: string;
  paypal_payout_id?: string;
  summary: string;
  payload: Record<string, any>;
  previous_hash: string;
  current_hash: string;
  created_at: string;
}

export interface ChainVerificationResult {
  is_valid: boolean;
  status: string;
  total_records: number;
  verified_at: string;
  broken_sequence_number?: number;
  expected_hash?: string;
  actual_hash?: string;
}

export interface ScenarioExecutionResult {
  scenario_id: string;
  name: string;
  scenario_type: 'ATTACK' | 'BENIGN';
  description: string;
  simulated_agent_mode: string;
  attempted_action: {
    recipient_email: string;
    amount_minor: number;
    currency: string;
  };
  policy_outcome: string;
  ai_risk_level: string;
  ai_injection_detected: boolean;
  final_decision: string;
  blocked_reason?: string;
  reached_paypal: boolean;
  evaluation_latency_ms: number;
}

export interface DashboardStats {
  active_mandate_title: string;
  active_mandate_version: number;
  weekly_limit_minor: number;
  weekly_spent_minor: number;
  weekly_utilization_percent: number;
  pending_approvals_count: number;
  submitted_payouts_count: number;
  confirmed_payouts_count: number;
  blocked_attacks_count: number;
  escalated_requests_count: number;
  paypal_connected: boolean;
  kill_switch_active: boolean;
  environment: string;
  recent_alerts: Array<{ id: string; title: string; severity: string; created_at: string }>;
  recent_audit_events: Array<{ seq: number; type: string; summary: string; hash: string }>;
}
