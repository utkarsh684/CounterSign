# COUNTERSIGN: Repository File Map

```
CounterSign/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint with lifespan, CORS, middleware, SSE
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic Settings (env vars, sandbox locks, JWT, PayPal, AI)
│   │   │   ├── security.py             # Argon2 password hashing, JWT creation/verification, API key hashing
│   │   │   ├── dependencies.py         # DB session, current owner user, authenticated agent dependencies
│   │   │   ├── exceptions.py           # Custom domain exceptions & global exception handlers
│   │   │   └── logging.py              # Redacted structured JSON logging
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py               # Aggregates /api/v1 routes
│   │   │   └── routes/
│   │   │       ├── auth.py             # /auth/register, /auth/login, /auth/me, /auth/logout
│   │   │       ├── mandates.py         # /mandates/compile, /mandates, /mandates/{id}/activate, /revoke
│   │   │       ├── payees.py           # /payees (CRUD, verify, block)
│   │   │       ├── invoices.py         # /invoices/upload, /invoices/{id}/analyze, /process
│   │   │       ├── agent.py            # /agent/process, /agent/run-scenario, /agent/status
│   │   │       ├── gateway.py          # /gateway/payments (evaluation & submission)
│   │   │       ├── approvals.py        # /approvals, /approvals/{id}/approve, /reject, /resolve
│   │   │       ├── paypal.py           # /paypal/status, /test-connection, /payments/{id}/reconcile
│   │   │       ├── webhooks.py         # /webhooks/paypal (signature verification & event processing)
│   │   │       ├── audit.py            # /audit, /audit/verify, /audit/{id}/evidence, /audit/export
│   │   │       ├── security.py         # /security/kill-switch, /status, /alerts
│   │   │       └── dashboard.py        # /dashboard/stats, /dashboard/stream (SSE)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # DeclarativeBase, UUIDPrimaryKey, TimestampMixin
│   │   │   ├── user.py                 # User, AgentApiKey
│   │   │   ├── mandate.py              # Mandate, MandateVersion
│   │   │   ├── payee.py                # Payee
│   │   │   ├── invoice.py              # Invoice, EvidenceDocument
│   │   │   ├── payment.py              # PaymentRequest, PolicyEvaluation, AIVerification
│   │   │   ├── approval.py             # ApprovalDecision
│   │   │   ├── paypal.py               # PayPalPayout, PayPalWebhookEvent
│   │   │   └── audit.py                # AuditEvent, SecurityAlert
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # Token, UserCreate, UserResponse, LoginRequest
│   │   │   ├── mandate.py              # MandateCreate, MandateCompileRequest, MandateResponse, MandateSpec
│   │   │   ├── payee.py                # PayeeCreate, PayeeUpdate, PayeeResponse
│   │   │   ├── invoice.py              # InvoiceUploadResponse, ExtractedInvoiceData, InvoiceResponse
│   │   │   ├── payment.py              # PaymentRequestCreate, PolicyEvaluationResponse, PaymentRequestResponse
│   │   │   ├── approval.py             # ApprovalRequest, ApprovalResponse, ConfirmationPayload
│   │   │   ├── audit.py                # AuditEventResponse, ChainVerificationResult, EvidencePackage
│   │   │   ├── agent.py                # AgentRunRequest, AgentActionResponse, ScenarioResult
│   │   │   └── paypal.py               # PayPalStatusResponse, WebhookVerificationRequest
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── session.py              # SQLAlchemy engine, sessionmaker, get_db generator
│   │   ├── policy/
│   │   │   ├── __init__.py
│   │   │   ├── money.py                # MinorUnit currency converters, decimal formatting
│   │   │   ├── rules.py                # 18 pure Python deterministic policy rules
│   │   │   ├── decision.py             # READY_FOR_APPROVAL, ESCALATE, DENY types
│   │   │   └── engine.py               # DeterministicPolicyEngine orchestration
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py             # AIProvider abstract base class
│   │   │   ├── gemini_provider.py      # Google Gemini provider adapter
│   │   │   ├── openai_provider.py      # OpenAI provider adapter
│   │   │   ├── anthropic_provider.py   # Anthropic Claude provider adapter
│   │   │   ├── fallback_provider.py    # Deterministic high-fidelity fallback provider
│   │   │   ├── mandate_compiler.py     # Converts natural language into validated MandateSpec
│   │   │   ├── invoice_analyzer.py     # Multimodal & text invoice extraction
│   │   │   ├── intent_verifier.py      # Independent AI intent & prompt injection verifier
│   │   │   └── approval_writer.py      # Advisory human-readable payment summaries
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── agent_tools.py          # ReadInbox, ReadInvoice, ListPayees, GetMandateSummary, RequestPayment
│   │   │   ├── ops_agent.py            # Live tool-calling Accounts Payable Agent
│   │   │   └── compromised_agent.py    # Scripted compromised agent for reproducible red-team demos
│   │   ├── paypal/
│   │   │   ├── __init__.py
│   │   │   ├── oauth.py                # PayPal OAuth 2.0 token manager with caching
│   │   │   ├── client.py               # Asynchronous HTTPX client for sandbox API
│   │   │   ├── payouts.py              # POST /v1/payments/payouts executor with idempotency
│   │   │   ├── webhooks.py             # PayPal webhook signature verification
│   │   │   └── reconciliation.py       # Payout status polling & webhook reconciliation
│   │   ├── ledger/
│   │   │   ├── __init__.py
│   │   │   ├── hash_chain.py           # SHA-256 append-only ledger hashing & chain verification
│   │   │   ├── audit_service.py        # Centralized audit logging service
│   │   │   └── evidence_export.py      # JSON and printable HTML/PDF evidence packages
│   │   └── redteam/
│   │       ├── __init__.py
│   │       └── scenarios.py            # 12 attack scenarios & 6 benign scenarios definitions
│   ├── alembic/                        # Database migration scripts
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Test database fixtures, mock providers
│   │   ├── test_policy_engine.py       # Table-driven unit tests for 18 policy rules
│   │   ├── test_hash_chain.py          # Hash-chain integrity & tamper detection tests
│   │   ├── test_paypal_client.py       # Mocked PayPal OAuth, Payouts, Webhook verification tests
│   │   ├── test_ai_verifier.py         # AI verifier schema & fail-closed tests
│   │   ├── test_api_endpoints.py       # Integration tests for FastAPI endpoints
│   │   └── test_redteam_runner.py      # Verifies 0 malicious attacks reach payout executor
│   ├── scripts/
│   │   ├── seed_demo.py                # Database seeder with demo owner, payees, invoices, mandates
│   │   ├── run_redteam.py              # CLI red-team scenario runner
│   │   └── paypal_smoke_test.py        # Direct PayPal sandbox OAuth and payout check
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css                   # Tailwind and custom fintech design system variables
│   │   ├── components/                 # Layout, Header, Sidebar, KillSwitchModal, StatusBadge, Cards
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx         # Enterprise fintech landing page
│   │   │   ├── DashboardPage.tsx       # Real-time financial metrics, spending utilization, SSE
│   │   │   ├── MandatesPage.tsx        # Natural-language mandate compiler & active mandate visualizer
│   │   │   ├── InvoicesPage.tsx        # Invoice upload, document preview, security findings
│   │   │   ├── AgentPage.tsx           # Ops Agent live run & step-by-step tool execution monitor
│   │   │   ├── PayeesPage.tsx          # Payee registry, email change guard, verification
│   │   │   ├── ApprovalsPage.tsx       # Approval queue, typed amount confirmation, exception handling
│   │   │   ├── InjectionLabPage.tsx    # Split-screen Red Team Arena, 18 scenarios & scoreboard
│   │   │   ├── AuditLedgerPage.tsx     # AG Grid tamper-evident ledger, chain verifier, evidence exporter
│   │   │   ├── PayPalSettingsPage.tsx  # PayPal Sandbox diagnostics, OAuth health, webhooks
│   │   │   └── LoginPage.tsx           # Owner login & demo account quick-fill
│   │   ├── services/                   # Axios/Fetch API client modules
│   │   ├── types/                      # TypeScript interfaces matching Pydantic schemas
│   │   └── utils/                      # Currency formatters, date formatters, hash helpers
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── RISK_REGISTER.md
│   ├── FILE_MAP.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PAYPAL_SETUP.md
│   ├── SECURITY.md
│   ├── API.md
│   └── DEMO.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```
