from fastapi import APIRouter
from modules.crm import service

router = APIRouter(prefix="/crm", tags=["crm"])


@router.get("/retention-cases")
def list_retention_cases(limit: int = 50):
    return service.list_retention_cases(limit=limit)
