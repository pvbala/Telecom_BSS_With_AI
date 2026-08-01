from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.assurance.models import Alarm, TroubleTicket


def raise_alarm(alarm_type: str, severity: str = "minor", description: str = "",
                 service_instance_id: int | None = None) -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, Alarm, "code")
        alarm = Alarm(code=f"ALM-{seq:04d}", service_instance_id=service_instance_id,
                       severity=severity, alarm_type=alarm_type, description=description)
        session.add(alarm)
        session.flush()
        result = {"alarm_id": alarm.id, "code": alarm.code, "severity": severity,
                  "alarm_type": alarm_type, "description": description,
                  "service_instance_id": service_instance_id}
    # This is the event that AI anomaly-detection/event_subscribers listens for (event-driven trigger)
    publish("alarm_raised", **result)
    return result


def create_ticket(subject: str, description: str, customer_id: int | None = None,
                   alarm_id: int | None = None) -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, TroubleTicket, "code")
        ticket = TroubleTicket(code=f"TCK-{seq:04d}", customer_id=customer_id, alarm_id=alarm_id,
                                subject=subject, description=description)
        session.add(ticket)
        session.flush()
        result = {"ticket_id": ticket.id, "code": ticket.code}
    publish("ticket_created", **result)
    return result


def list_alarms(limit: int = 50, alarm_type: str | None = None) -> list[dict]:
    with get_session() as session:
        q = session.query(Alarm)
        if alarm_type:
            q = q.filter(Alarm.alarm_type == alarm_type)
        rows = q.order_by(Alarm.id.desc()).limit(limit).all()
        return [{"id": a.id, "code": a.code, "severity": a.severity, "alarm_type": a.alarm_type,
                  "description": a.description, "status": a.status} for a in rows]


def list_tickets(limit: int = 50, customer_id: int | None = None) -> list[dict]:
    with get_session() as session:
        q = session.query(TroubleTicket)
        if customer_id:
            q = q.filter(TroubleTicket.customer_id == customer_id)
        rows = q.order_by(TroubleTicket.id.desc()).limit(limit).all()
        return [{"id": t.id, "code": t.code, "subject": t.subject, "status": t.status,
                  "customer_id": t.customer_id} for t in rows]