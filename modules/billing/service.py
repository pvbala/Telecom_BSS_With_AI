from datetime import datetime, timedelta, timezone
from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.billing.models import Invoice


def raise_invoice(account_id: int, amount: float, currency: str = "INR") -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, Invoice, "code")
        inv = Invoice(code=f"INV-{seq:04d}", account_id=account_id, amount=amount,
                       currency=currency, status="ISSUED",
                       due_at=datetime.now(timezone.utc) + timedelta(days=15))
        session.add(inv)
        session.flush()
        result = {"invoice_id": inv.id, "invoice_code": inv.code, "amount": amount,
                   "status": inv.status}
    publish("invoice_raised", **result, account_id=account_id)
    return result


def update_invoice_status(invoice_id: int, status: str) -> dict:
    """Used e.g. by the test data engine to mark invoices OVERDUE/PAID/DISPUTED
    so churn features (overdue_invoice_count) have real variety to train on."""
    with get_session() as session:
        inv = session.query(Invoice).get(invoice_id)
        if not inv:
            raise ValueError(f"Invoice {invoice_id} not found")
        inv.status = status
        session.flush()
        result = {"invoice_id": inv.id, "code": inv.code, "status": status}
    publish("invoice_status_changed", **result)
    return result


def mark_invoice_paid(invoice_id: int) -> dict:
    """
    Invoice Payment feature (Manage Entities): the simple, no-partial-payment
    version - just flips an invoice straight to PAID. This is the function
    the 'Mark as Paid' button calls.
    """
    result = update_invoice_status(invoice_id, "PAID")
    publish("invoice_paid", **result)
    return result


def list_invoices(account_id: int | None = None) -> list[dict]:
    with get_session() as session:
        q = session.query(Invoice)
        if account_id:
            q = q.filter(Invoice.account_id == account_id)
        rows = q.order_by(Invoice.id.desc()).all()
        return [{"id": i.id, "code": i.code, "amount": i.amount, "status": i.status,
                  "account_id": i.account_id} for i in rows]


def raise_invoice_for_account(account_id: int) -> dict:
    """
    Sums all rated usage charges for the given account's customer and
    raises one invoice for that total. Shared by the manual 'Raise
    Invoice' screen; the Test Data Engine's raise_invoice step does the
    same summation across a whole run instead of one account at a time.
    """
    from modules.party.models import Account
    from modules.inventory.models import ProductInstance
    from modules.mediation_rating import service as mediation_service
    from core.db import get_session as _get_session

    with _get_session() as session:
        acc = session.query(Account).get(account_id)
        if not acc:
            raise ValueError(f"Account {account_id} not found")
        customer_id = acc.customer_id
        pi_ids = [p.id for p in session.query(ProductInstance)
                  .filter(ProductInstance.customer_id == customer_id).all()]

    total = sum(mediation_service.get_total_charges(pid) for pid in pi_ids)
    return raise_invoice(account_id=account_id, amount=round(total, 2))