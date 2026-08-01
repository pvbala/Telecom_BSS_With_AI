from fastapi import APIRouter
from pydantic import BaseModel
from modules.assurance import service

router = APIRouter(prefix="/assurance", tags=["assurance"])


class RaiseAlarmRequest(BaseModel):
    alarm_type: str
    severity: str = "minor"
    description: str = ""
    service_instance_id: int | None = None


@router.post("/alarms")
def raise_alarm(req: RaiseAlarmRequest):
    return service.raise_alarm(**req.model_dump())


@router.get("/alarms")
def list_alarms(limit: int = 50):
    return service.list_alarms(limit=limit)


@router.get("/tickets")
def list_tickets(limit: int = 50):
    return service.list_tickets(limit=limit)
