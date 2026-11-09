"""Invoice Understanding and Document Extraction Service.

Extracts structured financial fields and detects prompt injection, social engineering,
and recipient overrides in untrusted third-party invoices.
"""

import io
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from pypdf import PdfReader
from app.policy.money import dollars_to_minor_units
from app.schemas.invoice import ExtractedInvoiceData, InvoiceFinding


class InvoiceAnalyzerService:
    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """Extracts raw text stream from PDF using pypdf."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception:
            return ""

    @classmethod
    def analyze_invoice_text(cls, raw_text: str, filename: str = "invoice.pdf") -> ExtractedInvoiceData:
        """Parses untrusted document text with multi-layer adversarial injection scans."""
        findings: List[InvoiceFinding] = []
        text_lower = raw_text.lower()

        # 1. Check for prompt injection / financial override attempts
        injection_triggers = [
            ("ignore previous", "INSTRUCTION_OVERRIDE", "Attempts to override system instructions"),
            ("banking details have changed", "DESTINATION_ALTERATION", "Unverified bank/destination change"),
            ("send to billing@", "RECIPIENT_REDIRECT", "Explicit redirection cue"),
            ("mark this payment as approved", "FALSE_AUTHORITY", "Claims fabricated owner authorization"),
            ("approved by the owner", "FALSE_AUTHORITY", "Claims owner authorization in invoice text"),
            ("urgent wire", "SOCIAL_ENGINEERING", "High-pressure urgency coercion"),
        ]

        for cue, category, desc in injection_triggers:
            if cue in text_lower:
                # Find matching context snippet
                start = max(0, text_lower.find(cue) - 20)
                end = min(len(raw_text), text_lower.find(cue) + len(cue) + 40)
                snippet = raw_text[start:end].strip().replace("\n", " ")
                findings.append(
                    InvoiceFinding(
                        category=category,
                        severity="CRITICAL",
                        title=f"Potential Adversarial Instruction: '{cue}'",
                        description=f"{desc}. Invoices must never dictate owner policy.",
                        evidence_snippet=snippet,
                    )
                )

        # 2. Extract vendor email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        vendor_email = email_match.group(0) if email_match else "unknown@vendor.example"

        # Check for destination redirect in payment instructions
        redirect_email = re.search(r"(?:send|remit|pay|to)\s+(?:to\s+)?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", raw_text, re.IGNORECASE)
        if redirect_email and redirect_email.group(1).lower() != vendor_email.lower():
            findings.append(
                InvoiceFinding(
                    category="DESTINATION_DISCREPANCY",
                    severity="CRITICAL",
                    title="Payee Redirection Mismatch",
                    description=f"Invoice vendor is '{vendor_email}' but text requests payment to '{redirect_email.group(1)}'.",
                    evidence_snippet=redirect_email.group(0),
                )
            )

        # 3. Extract Invoice Number
        inv_match = re.search(r"(?:invoice\s*(?:#|no\.?|number)?\s*[:\-\s]*)([A-Z0-9\-]+)", raw_text, re.IGNORECASE)
        invoice_number = inv_match.group(1) if inv_match else "INV-9999"

        # 4. Extract Amount
        amount_matches = re.findall(r"\$\s*(\d+(?:,\d+)*(?:\.\d{2})?)", raw_text)
        if amount_matches:
            # Pick the largest amount as the likely total
            numeric_amounts = [float(a.replace(",", "")) for a in amount_matches]
            total_amount_minor = dollars_to_minor_units(max(numeric_amounts))
        else:
            total_amount_minor = 6000  # Default $60

        # 5. Extract Vendor Name
        vendor_match = re.search(r"(?:from|vendor|contractor|company):\s*([A-Za-z0-9\s&,.-]+)", raw_text, re.IGNORECASE)
        vendor_name = vendor_match.group(1).strip() if vendor_match else "Contractor Services"

        return ExtractedInvoiceData(
            vendor_name=vendor_name,
            vendor_email=vendor_email,
            invoice_number=invoice_number,
            issue_date=date.today(),
            due_date=date.today(),
            currency="USD",
            total_amount_minor=total_amount_minor,
            tax_amount_minor=0,
            payment_instructions=raw_text[:200],
            findings=findings,
        )
