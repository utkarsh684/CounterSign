import { Link } from 'react-router-dom';
import { Shield, ArrowRight, Lock, Eye, Zap, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

const features = [
  {
    icon: Lock,
    title: 'Natural-Language Mandates',
    desc: 'Define spending rules in plain English. AI compiles them into deterministic policy constraints.',
  },
  {
    icon: ShieldCheck,
    title: '18-Rule Policy Engine',
    desc: 'Every payment request passes through 18 deterministic security rules before reaching PayPal.',
  },
  {
    icon: Eye,
    title: 'AI Security Verifier',
    desc: 'Independent AI double-checks every transaction for prompt injection, social engineering, and fraud.',
  },
  {
    icon: Zap,
    title: 'Tamper-Evident Audit Ledger',
    desc: 'SHA-256 hash-chained audit trail. Every event is cryptographically linked and verifiable.',
  },
];

export default function Landing() {
  return (
    <div className="landing-page">
      <header style={{ padding: '20px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#fff' }}>
          <div style={{
            width: 32, height: 32, background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
            borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Shield size={17} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.02em' }}>Countersign</span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link to="/login" className="landing-cta secondary">Sign In</Link>
          <Link to="/register" className="landing-cta primary">Get Started</Link>
        </div>
      </header>

      <section className="landing-hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="env-badge sandbox" style={{ marginBottom: 24 }}>
            <span className="dot"></span>
            SANDBOX ENVIRONMENT
          </div>
          <h1>Give your AI agent<br />a spending mandate,<br />not your wallet.</h1>
          <p>
            Countersign is the trust and security layer that sits between your AI agent
            and PayPal. Define financial rules in natural language, enforce them with
            deterministic policy checks, and maintain a tamper-evident audit trail.
          </p>
          <div className="cta-group">
            <Link to="/register" className="landing-cta primary">
              <ArrowRight size={16} style={{ marginRight: 6 }} />
              Launch Dashboard
            </Link>
            <Link to="/login" className="landing-cta secondary">
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      <section style={{ padding: '60px 32px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24 }}>
          {features.map((feat, i) => (
            <motion.div
              key={feat.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 12,
                padding: '28px 24px',
              }}
            >
              <feat.icon size={28} style={{ color: '#60A5FA', marginBottom: 16 }} />
              <h3 style={{ color: '#fff', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>{feat.title}</h3>
              <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.6 }}>{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer style={{ textAlign: 'center', padding: '40px 24px', color: '#475569', fontSize: 13 }}>
        COUNTERSIGN · Sandbox Environment · Not a production financial product
      </footer>
    </div>
  );
}
