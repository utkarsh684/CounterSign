"""Pydantic schemas for Invoice and Evidence processing."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InvoiceFinding(BaseModel):
    category: str
    severity: str  # INFO, WARNING, CRITICAL
    title: str
    description: str
    evidence_snippet: Optional[str] = None
    line_number: Optional[int] = None


class ExtractedInvoiceData(BaseModel):
    vendor_name: str
    vendor_email: str
    invoice_number: str
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: str = "USD"
    total_amount_minor: int
    tax_amount_minor: int = 0
    payment_instructions: Optional[str] = None
    findings: List[InvoiceFinding] = Field(default_factory=list)


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    vendor_name: str
    vendor_email: str
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: str
    total_amount_minor: int
    tax_amount_minor: int
    file_sha256: str
    payment_instructions: Optional[str] = None
    status: str
    extracted_metadata: Dict[str, Any]
    security_findings: List[Dict[str, Any]]
    created_at: datetime
