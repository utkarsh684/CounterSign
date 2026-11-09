# COUNTERSIGN: System Architecture

```mermaid
graph TD
    subgraph ClientLayer ["Client & Interface Layer"]
        Owner["Business Owner / FinOps"]
        Dashboard["React Dashboard (TypeScript + Vite + Tailwind + AG Grid)"]
        Landing["Enterprise SaaS Landing Page"]
        InjectionArena["Injection Lab / Red Team Arena (12 Attacks vs 6 Benign)"]
        AuditLedger["Hash-Chained Audit Ledger (SHA-256 Chain Verification)"]
    end

    subgraph APILayer ["FastAPI Gateway & Security Boundary"]
        FastAPI["FastAPI 0.115+ REST & SSE Engine"]
        AuthMiddleware["Auth & RBAC (Argon2, JWT, Agent API Keys)"]
        KillSwitch["Global Security Kill Switch (Hardware-style Override)"]
        RateLimiter["Adaptive Financial Rate Limiter"]
    end

    subgraph IntelligenceLayer ["Agent & AI Verification Layer"]
        OpsAgent["Countersign Ops Agent (Tool-Calling ReAct AP Assistant)"]
        CompromisedAgent["Scripted Compromised Agent (Deterministic Red-Team Simulator)"]
        AICompiler["AI Spending Mandate Compiler (Gemini / OpenAI / Claude)"]
        InvoiceProcessor["Multimodal Invoice Extractor (PyMuPDF / OCR / LLM)"]
        AIVerifier["Independent AI Security Verifier (Intent & Injection Guard)"]
    end

    subgraph PolicyEngine ["Deterministic Financial Policy Engine (Zero-LLM Authority)"]
        PolicyGate{"Deterministic Policy Gate"}
        Rules["18 Pure Python Policy Rules
        - Mandate Active & Not Expired
        - Kill Switch Inactive
        - Supported Currency & Valid Integer Minor Units
        - Per-Payment, Daily & Weekly Cumulative Limits
        - Allowed Weekdays & Operating Hours
        - Payee Email Tamper Detection (Hard Reject)
        - Duplicate Invoice & Request Idempotency
        - Invoice vs Request Amount Exact Match
        - Evidence Provenance & Trust Level"]
        DecisionModel["Decision Model:
        READY_FOR_APPROVAL | ESCALATE | DENY"]
    end

    subgraph HumanApprovalLayer ["Explicit Human Authorization Layer"]
        ApprovalCenter["Payment Approval Center"]
        TypedConfirmation["Double-Check & High-Value Typed Re-verification"]
        OneTimeException["Scoped One-Time Soft Limit Waiver"]
    end

    subgraph ExecutionLayer ["PayPal Financial Execution Gateway"]
        RevalidationCheck{"Pre-Execution Re-verification"}
        PayPalClient["PayPal HTTPX Client (Sandbox REST API)"]
        PayoutsAPI["POST /v1/payments/payouts (Batch & Item Payouts)"]
        OAuthMgr["OAuth 2.0 Token Acquisition & In-Memory Cache"]
        Reconciliation["Webhook Ingestion & Status Poller"]
    end

    subgraph LedgerStorage ["Storage & Audit Ledger"]
        MySQL[("MySQL 8.4 Enterprise Database")]
        Alembic["Alembic Migrations"]
        HashChain["SHA-256 Tamper-Evident Hash Chain"]
    end

    Owner -->|Configures Mandates / Reviews / Approves| Dashboard
    Dashboard --> FastAPI
    Landing --> Dashboard
    InjectionArena --> FastAPI
    AuditLedger --> FastAPI

    FastAPI --> AuthMiddleware
    AuthMiddleware --> KillSwitch
    KillSwitch --> RateLimiter

    RateLimiter --> OpsAgent
    RateLimiter --> CompromisedAgent
    OpsAgent --> InvoiceProcessor
    OpsAgent -->|Propose Payment Request| PolicyGate
    CompromisedAgent -->|Attempt Manipulated Payment| PolicyGate

    AICompiler -->|Outputs Strict Pydantic Mandate| PolicyGate

    PolicyGate --> Rules
    Rules --> DecisionModel
    DecisionModel -->|Non-DENY Candidate| AIVerifier
    AIVerifier -->|Advisory Security Risk Assessment| ApprovalCenter

    ApprovalCenter -->|Explicit Human Sign-Off| TypedConfirmation
    TypedConfirmation --> RevalidationCheck

    RevalidationCheck -->|Re-verifies Mandate, Payee & Non-Tamper| PayPalClient
    PayPalClient --> OAuthMgr
    PayPalClient --> PayoutsAPI

    PayoutsAPI -->|Returns Batch ID & SUBMITTED Status| Reconciliation
    Reconciliation -->|Verifies PayPal-Transmission-Sig & Status| HashChain

    FastAPI --> MySQL
    PolicyGate --> MySQL
    HashChain --> MySQL
```

## Security Boundaries & Critical Guarantees

1. **AI Proposes, Deterministic Rules Enforce, Humans Authorize, PayPal Executes**:
   - The AI agent has **zero access** to PayPal client credentials, direct payout execution tools, database modification APIs, or mandate overrides.
   - The AI Verifier can only make policy decisions stricter (e.g. `READY_FOR_APPROVAL` -> `ESCALATE`), never override a deterministic `DENY`.

2. **Sandbox-Only Lock**:
   - Hardcoded sandbox endpoint `https://api-m.sandbox.paypal.com`.
   - Never exposes live endpoints or executes live funds in this hackathon build.

3. **Tamper-Evident Audit Ledger**:
   - Every single event (mandate activation, invoice analysis, gateway evaluation, verifier audit, human approval, PayPal payout submission, webhook event) is chained with `sha256(prev_hash + canonical_event_json)`.
   - Any manual edit in the database breaks the chain verification instantly (`CHAIN INTEGRITY: COMPROMISED`).
