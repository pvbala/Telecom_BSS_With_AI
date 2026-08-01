"""Simulated usage collection — generates synthetic CDRs for active services,
and deducts prepaid balance in real time.
"""
import random
from decimal import Decimal
from billing.models import Balance, LedgerEntry
from .models import UsageRecord


def generate_usage_for_service(service):
    order = service.order
    product_type = order.price_plan.product.product_type

    if product_type == "PREPAID_SIM":
        usage_type = random.choice(["DATA", "VOICE", "SMS"])
        data_mb = round(random.uniform(5, 200), 2) if usage_type == "DATA" else 0
        duration = random.randint(10, 600) if usage_type == "VOICE" else 0
        charge = Decimal(str(round(data_mb * 0.02 if usage_type == "DATA" else duration * 0.01, 2)))

        record = UsageRecord.objects.create(
            service=service, usage_type=usage_type, data_mb=data_mb,
            duration_seconds=duration, charge_amount=charge,
        )

        balance = Balance.objects.filter(order=order).first()
        if balance:
            balance.amount = max(Decimal("0"), balance.amount - charge)
            if usage_type == "DATA":
                balance.data_remaining_gb = max(0.0, balance.data_remaining_gb - data_mb / 1024)
            balance.save(update_fields=["amount", "data_remaining_gb", "updated_at"])
            LedgerEntry.objects.create(
                balance=balance, entry_type="USAGE_DEDUCTION", amount=charge,
                description=f"{usage_type} usage",
            )
        return record

    else:  # FIBER — just log bandwidth usage, no per-use billing
        data_mb = round(random.uniform(100, 5000), 2)
        return UsageRecord.objects.create(
            service=service, usage_type="DATA", data_mb=data_mb, charge_amount=Decimal("0")
        )
