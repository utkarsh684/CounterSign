"""Invoice Inbox and Document Processing Routes."""

import hashlib
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.ai.invoice_analyzer import InvoiceAnalyzerService
from app.core.dependencies import get_current_owner, get_db
from app.ledger.audit_service import AuditService
from app.models.invoice import EvidenceDocument, Invoice
from app.models.user import User
from app.schemas.invoice import InvoiceResponse

router = APIRouter(prefix="/invoices", tags=["Invoice Inbox"])


@router.post("/upload", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: UploadFile = File(...),
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    file_sha256 = hashlib.sha256(content).hexdigest()

    # Extract text from PDF or raw bytes
    filename = file.filename or "invoice.pdf"
    if filename.lower().endswith(".pdf"):
        extracted_text = InvoiceAnalyzerService.extract_text_from_pdf(content)
    else:
        try:
            extracted_text = content.decode("utf-8", errors="ignore")
        except Exception:
            extracted_text = "Binary invoice document"

    # Analyze text & adversarial cues
    analysis = InvoiceAnalyzerService.analyze_invoice_text(extracted_text, filename=filename)

    invoice = Invoice(
        user_id=owner.id,
        invoice_number=analysis.invoice_number,
        vendor_name=analysis.vendor_name,
        vendor_email=analysis.vendor_email,
        issue_date=analysis.issue_date,
        due_date=analysis.due_date,
        currency=analysis.currency,
        total_amount_minor=analysis.total_amount_minor,
        tax_amount_minor=analysis.tax_amount_minor,
        file_sha256=file_sha256,
        raw_text=extracted_text[:10000],
        payment_instructions=analysis.payment_instructions,
        status="ANALYZED",
        extracted_metadata={
            "vendor_name": analysis.vendor_name,
            "vendor_email": analysis.vendor_email,
            "invoice_number": analysis.invoice_number,
        },
        security_findings=[f.model_dump() for f in analysis.findings],
    )
    db.add(invoice)
    db.flush()

    # Attach evidence document record
    evidence = EvidenceDocument(
        invoice_id=invoice.id,
        evidence_type="INVOICE_PDF" if filename.lower().endswith(".pdf") else "INVOICE_DOCUMENT",
        source_uri=f"uploads/{filename}",
        sha256_checksum=file_sha256,
        trust_level="HIGH" if not analysis.findings else "UNTRUSTED_THIRD_PARTY",
        extracted_snippets=[f.evidence_snippet for f in analysis.findings if f.evidence_snippet],
    )
    db.add(evidence)
    db.commit()
    db.refresh(invoice)

    AuditService.record_event(
        db=db,
        event_type="INVOICE_INGESTED",
        summary=f"Ingested Invoice #{invoice.invoice_number} ({invoice.vendor_name})",
        payload={
            "invoice_id": invoice.id,
            "vendor_name": invoice.vendor_name,
            "amount_minor": invoice.total_amount_minor,
            "findings_count": len(analysis.findings),
            "sha256": file_sha256,
        },
        user_id=owner.id,
    )

    return InvoiceResponse.model_validate(invoice)


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(owner: User = Depends(get_current_owner), db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.user_id == owner.id).order_by(Invoice.created_at.desc()).all()
    return [InvoiceResponse.model_validate(inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, owner: User = Depends(get_current_owner), db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == owner.id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(inv)
