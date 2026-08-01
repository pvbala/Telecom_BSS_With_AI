from fastapi import APIRouter
from pydantic import BaseModel
from modules.catalog import service

router = APIRouter(prefix="/catalog", tags=["catalog"])


class CreateSpecRequest(BaseModel):
    name: str
    category: str
    characteristic_schema: list


class CreateOfferingRequest(BaseModel):
    name: str
    spec_id: int
    price: float
    currency: str = "INR"
    billing_frequency: str = "monthly"


@router.post("/specs")
def create_spec(req: CreateSpecRequest):
    return service.create_product_spec(**req.model_dump())


@router.post("/offerings")
def create_offering(req: CreateOfferingRequest):
    return service.create_offering(**req.model_dump())


@router.get("/offerings")
def list_offerings():
    return service.list_offerings()
