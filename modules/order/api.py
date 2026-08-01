from fastapi import APIRouter
from pydantic import BaseModel
from modules.order import service

router = APIRouter(prefix="/orders", tags=["order"])


class PlaceOrderRequest(BaseModel):
    customer_id: int
    account_id: int
    items: list[dict]
    channel: str = "online"


@router.post("")
def place_order(req: PlaceOrderRequest):
    return service.place_order(**req.model_dump())


@router.get("")
def list_orders(limit: int = 100):
    return service.list_orders(limit=limit)


@router.get("/{order_id}")
def get_order(order_id: int):
    return service.get_order(order_id)
