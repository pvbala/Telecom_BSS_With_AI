from fastapi import APIRouter
from modules.inventory import service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/product-instances")
def list_product_instances(customer_id: int | None = None):
    return service.list_product_instances(customer_id=customer_id)
