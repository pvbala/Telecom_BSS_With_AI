from fastapi import APIRouter
from pydantic import BaseModel
from modules.party import service

router = APIRouter(prefix="/party", tags=["party"])


class CreateCustomerRequest(BaseModel):
    name: str
    customer_type: str = "individual"
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    segment: str = "consumer"
    credit_profile: dict = {}


@router.post("/customers")
def create_customer(req: CreateCustomerRequest):
    return service.create_customer(**req.model_dump())


@router.get("/customers")
def list_customers(limit: int = 100):
    return service.list_customers(limit=limit)


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    return service.get_customer(customer_id)
