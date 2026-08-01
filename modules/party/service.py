from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.party.models import Customer, Account


def create_customer(name: str, customer_type: str = "individual", email: str = None,
                     phone: str = None, address: str = None, segment: str = "consumer",
                     credit_profile: dict = None) -> dict:
    """Additive: always inserts a new row; code continues from existing count."""
    with get_session() as session:
        seq = next_sequence_number(session, Customer, "code")
        customer = Customer(
            code=f"CUST-{seq:04d}",
            customer_type=customer_type,
            name=name,
            email=email,
            phone=phone,
            address=address,
            segment=segment,
            credit_profile=credit_profile or {},
        )
        session.add(customer)
        session.flush()

        acc_seq = next_sequence_number(session, Account, "code")
        account = Account(code=f"ACC-{acc_seq:04d}", customer_id=customer.id)
        session.add(account)
        session.flush()

        result = {
            "customer_id": customer.id,
            "customer_code": customer.code,
            "account_id": account.id,
            "account_code": account.code,
            "name": customer.name,
        }
    publish("customer_created", **result)
    return result


def list_customers(limit: int = 100) -> list[dict]:
    with get_session() as session:
        rows = session.query(Customer).order_by(Customer.id.desc()).limit(limit).all()
        return [
            {"id": c.id, "code": c.code, "name": c.name, "segment": c.segment,
             "email": c.email, "phone": c.phone, "created_at": str(c.created_at)}
            for c in rows
        ]


def get_customer(customer_id: int) -> dict | None:
    with get_session() as session:
        c = session.query(Customer).get(customer_id)
        if not c:
            return None
        return {"id": c.id, "code": c.code, "name": c.name, "segment": c.segment,
                "email": c.email, "phone": c.phone}


def get_account_for_customer(customer_id: int) -> dict | None:
    with get_session() as session:
        a = session.query(Account).filter(Account.customer_id == customer_id).first()
        if not a:
            return None
        return {"id": a.id, "code": a.code, "customer_id": a.customer_id, "status": a.status}
