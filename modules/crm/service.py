from core.db import get_session, next_sequence_number
from core.event_bus import publish, subscribe
from modules.crm.models import RetentionCase


def create_retention_case(customer_id: int, churn_score: float, reason: str = "") -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, RetentionCase, "code")
        case = RetentionCase(code=f"RET-{seq:04d}", customer_id=customer_id,
                              churn_score=churn_score, reason=reason)
        session.add(case)
        session.flush()
        result = {"case_id": case.id, "code": case.code}
    publish("retention_case_created", **result, customer_id=customer_id)
    return result


def list_retention_cases(limit: int = 50) -> list[dict]:
    with get_session() as session:
        rows = session.query(RetentionCase).order_by(RetentionCase.id.desc()).limit(limit).all()
        return [{"id": c.id, "code": c.code, "customer_id": c.customer_id,
                  "churn_score": c.churn_score, "reason": c.reason, "status": c.status}
                for c in rows]


def _on_churn_score_ready(sender, **kwargs):
    """Auto-flag high-risk customers for retention, independent of any dashboard being open."""
    score = kwargs.get("score", 0)
    if score >= 0.7:
        create_retention_case(
            customer_id=kwargs["customer_id"],
            churn_score=score,
            reason=kwargs.get("reason", "High churn risk score"),
        )


def register_event_subscribers():
    subscribe("churn_score_ready", _on_churn_score_ready)
