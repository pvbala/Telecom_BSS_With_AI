import random
from datetime import datetime, timedelta, timezone
from core.db import get_session
from core.event_bus import publish
from modules.mediation_rating.models import UsageRecord, RatedCharge

RATE_PER_UNIT = {"data_mb": 0.05, "voice_min": 0.5, "sms": 0.2}

USAGE_PROFILES = {
    "light_user": {"data_mb": (100, 500), "voice_min": (10, 60), "sms": (0, 20)},
    "moderate_data_user": {"data_mb": (1000, 4000), "voice_min": (30, 120), "sms": (0, 30)},
    "heavy_user": {"data_mb": (5000, 15000), "voice_min": (60, 300), "sms": (0, 50)},
}


def generate_usage(product_instance_id: int, profile: str = "moderate_data_user",
                    duration_days: int = 30) -> dict:
    """Generates plausible daily usage records over a period - feeds billing AND AI models."""
    ranges = USAGE_PROFILES.get(profile, USAGE_PROFILES["moderate_data_user"])
    now = datetime.now(timezone.utc)
    total_amount = 0.0
    records_created = 0

    with get_session() as session:
        for day in range(duration_days):
            event_date = now - timedelta(days=duration_days - day)
            for usage_type, (lo, hi) in ranges.items():
                qty = round(random.uniform(lo, hi) / duration_days, 2)
                if qty <= 0:
                    continue
                ur = UsageRecord(product_instance_id=product_instance_id, usage_type=usage_type,
                                  quantity=qty, event_date=event_date)
                session.add(ur)
                session.flush()
                amount = round(qty * RATE_PER_UNIT.get(usage_type, 0.1), 2)
                rc = RatedCharge(usage_record_id=ur.id, product_instance_id=product_instance_id,
                                  amount=amount)
                session.add(rc)
                total_amount += amount
                records_created += 1

    result = {"product_instance_id": product_instance_id, "records_created": records_created,
               "total_amount": round(total_amount, 2)}
    publish("usage_generated", **result)
    return result


def get_total_charges(product_instance_id: int) -> float:
    with get_session() as session:
        rows = session.query(RatedCharge).filter(
            RatedCharge.product_instance_id == product_instance_id).all()
        return round(sum(r.amount for r in rows), 2)
