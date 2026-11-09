"""API router aggregating all version 1 endpoints."""

from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.mandates import router as mandates_router
from app.api.routes.payees import router as payees_router
from app.api.routes.invoices import router as invoices_router
from app.api.routes.agent import router as agent_router
from app.api.routes.gateway import router as gateway_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.paypal import router as paypal_router
from app.api.routes.audit import router as audit_router
from app.api.routes.security import router as security_router
from app.api.routes.dashboard import router as dashboard_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(mandates_router)
api_v1_router.include_router(payees_router)
api_v1_router.include_router(invoices_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(gateway_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(paypal_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(security_router)
api_v1_router.include_router(dashboard_router)
