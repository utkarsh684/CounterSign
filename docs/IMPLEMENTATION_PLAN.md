# COUNTERSIGN: Implementation Plan & Milestones

### Phase 0: Workspace Setup & Specification
- [x] Workspace inspection (Node v22, Python 3.13, MySQL 8.0 running on port 3306).
- [x] Dedicated clean Git repository initialized.
- [x] Architecture specification (`docs/ARCHITECTURE.md`).
- [x] Database schema specification (`docs/DATABASE_SCHEMA.md`).
- [x] Security risk register & threat model (`docs/RISK_REGISTER.md`).
- [x] Repository file map (`docs/FILE_MAP.md`).

### Phase 1: Python FastAPI Backend Foundation
- [ ] Requirements specification (`requirements.txt`, `pyproject.toml`).
- [ ] Virtual environment setup and dependency installation.
- [ ] Core configuration with Pydantic Settings (`app/core/config.py`).
- [ ] SQLAlchemy 2.0 async/sync engine, session management (`app/database/session.py`).
- [ ] Complete declarative models (`app/models/*.py`).
- [ ] Password hashing (Argon2id) and JWT security tokens (`app/core/security.py`).
- [ ] FastAPI application setup with CORS, exception handling, and `/health` route (`app/main.py`).
- [ ] Alembic setup and initial database schema generation.

### Phase 2: React TypeScript Frontend Foundation
- [ ] Vite + React + TypeScript scaffolding.
- [ ] Tailwind CSS with Linear/Stripe-inspired enterprise fintech design tokens.
- [ ] AG Grid Community installation & theme styling.
- [ ] Lucide icons, Framer Motion, TanStack Query, React Hook Form, Zod.
- [ ] Navigation sidebar, top bar with `SANDBOX` badge, global Kill Switch indicator.
- [ ] API client services with type-safe backend integration.

### Phase 3: Mandates & Payees Modules
- [ ] Pydantic schemas for mandates, constraints, and payees.
- [ ] Mandate compiler with ambiguity detection & rule explanation breakdown.
- [ ] Mandate versioning, HMAC authorization, revocation endpoints.
- [ ] Payee registry with email change hard-rejection policy.

### Phase 4: Deterministic Policy Engine
- [ ] Minor unit integer currency converter (`app/policy/money.py`).
- [ ] 18 pure Python deterministic policy rules (`app/policy/rules.py`).
- [ ] `DeterministicPolicyEngine` evaluation logic returning `READY_FOR_APPROVAL`, `ESCALATE`, or `DENY`.
- [ ] Comprehensive pytest unit test suite covering every single rule and boundary condition.

### Phase 5: PayPal Sandbox Integration
- [ ] OAuth 2.0 token acquisition and caching client (`app/paypal/oauth.py`).
- [ ] PayPal asynchronous HTTPX client targeting `https://api-m.sandbox.paypal.com`.
- [ ] Payouts executor (`POST /v1/payments/payouts`) with idempotency headers.
- [ ] Webhook signature verification (`app/paypal/webhooks.py`).
- [ ] Status reconciliation poller and webhook handler.
- [ ] Sandbox smoke test script (`scripts/paypal_smoke_test.py`).

### Phase 6: AI Integration Layer
- [ ] Abstract `AIProvider` base class with Gemini, OpenAI, Claude, and deterministic fallback implementations.
- [ ] Natural-language mandate compiler service.
- [ ] Multimodal & PDF invoice analyzer (PyMuPDF / regex / vision).
- [ ] Independent AI Security Verifier with strict Pydantic output schema.
- [ ] AI Operations Agent with ReAct tool-calling architecture.

### Phase 7: Approvals Center & Tamper-Evident Ledger
- [ ] Human approval endpoints with re-validation and typed amount confirmation for high-value payouts.
- [ ] Global Kill Switch toggle with immediate gateway blocking.
- [ ] SHA-256 hash-chained audit ledger (`app/ledger/hash_chain.py`).
- [ ] Chain verification algorithm and tamper detection.
- [ ] Evidence package JSON and printable HTML exporter.

### Phase 8: Injection Lab (Red-Team Arena)
- [ ] 12 attack scenarios + 6 benign scenarios definitions (`app/redteam/scenarios.py`).
- [ ] Scripted compromised agent for reproducible red-team demonstrations.
- [ ] Attack scoreboard calculation (0 malicious requests reach PayPal).
- [ ] CLI red-team runner (`scripts/run_redteam.py`).
- [ ] React split-screen comparison interface.

### Phase 9: Testing, Polish & Documentation
- [ ] 60+ automated backend and frontend tests.
- [ ] Seed script (`scripts/seed_demo.py`) with rich sample data.
- [ ] Docker Compose (`docker-compose.yml`), `.env.example`, `render.yaml`.
- [ ] Complete documentation suite (`README.md`, `PAYPAL_SETUP.md`, `SECURITY.md`, `API.md`, `DEMO.md`).
