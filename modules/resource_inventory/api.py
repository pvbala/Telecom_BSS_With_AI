from fastapi import APIRouter
from modules.resource_inventory import service

router = APIRouter(prefix="/resource-inventory", tags=["resource_inventory"])


@router.get("/summary")
def resource_summary():
    return service.summary()