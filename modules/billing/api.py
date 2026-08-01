from fastapi import APIRouter
from modules.billing import service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/invoices")
def list_invoices(account_id: int | None = None):
    return service.list_invoices(account_id=account_id)
