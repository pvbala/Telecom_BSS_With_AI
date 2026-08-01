from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.catalog.models import ProductSpecification, ProductOffering


class AttributeValidationError(Exception):
    pass


def create_product_spec(name: str, category: str, characteristic_schema: list) -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, ProductSpecification, "code")
        spec = ProductSpecification(
            code=f"SPEC-{seq:04d}", name=name, category=category,
            characteristic_schema=characteristic_schema,
        )
        session.add(spec)
        session.flush()
        result = {"spec_id": spec.id, "spec_code": spec.code, "name": spec.name}
    publish("product_spec_created", **result)
    return result


def create_offering(name: str, spec_id: int, price: float, currency: str = "INR",
                     billing_frequency: str = "monthly") -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, ProductOffering, "code")
        offering = ProductOffering(
            code=f"OFF-{seq:04d}", name=name, spec_id=spec_id, price=price,
            currency=currency, billing_frequency=billing_frequency,
        )
        session.add(offering)
        session.flush()
        result = {"offering_id": offering.id, "offering_code": offering.code, "name": offering.name}
    publish("product_offering_created", **result)
    return result


def list_offerings() -> list[dict]:
    with get_session() as session:
        rows = session.query(ProductOffering).all()
        return [
            {"id": o.id, "code": o.code, "name": o.name, "price": o.price,
             "currency": o.currency, "spec_id": o.spec_id}
            for o in rows
        ]


def get_offering_by_name(name: str) -> dict | None:
    with get_session() as session:
        o = session.query(ProductOffering).filter(ProductOffering.name == name).first()
        if not o:
            return None
        spec = session.query(ProductSpecification).get(o.spec_id)
        return {
            "id": o.id, "code": o.code, "name": o.name, "price": o.price,
            "spec_id": o.spec_id,
            "characteristic_schema": spec.characteristic_schema if spec else [],
        }


def get_offering_by_id(offering_id: int) -> dict | None:
    with get_session() as session:
        o = session.query(ProductOffering).get(offering_id)
        if not o:
            return None
        spec = session.query(ProductSpecification).get(o.spec_id)
        return {
            "id": o.id, "code": o.code, "name": o.name, "price": o.price,
            "spec_id": o.spec_id,
            "characteristic_schema": spec.characteristic_schema if spec else [],
        }


def list_product_specs() -> list[dict]:
    with get_session() as session:
        rows = session.query(ProductSpecification).all()
        return [{"id": s.id, "code": s.code, "name": s.name, "category": s.category,
                  "characteristic_schema": s.characteristic_schema} for s in rows]


def validate_attributes(spec_id: int, attributes: dict) -> dict:
    """Validates a set of attribute values against the ProductSpecification's schema."""
    with get_session() as session:
        spec = session.query(ProductSpecification).get(spec_id)
        if not spec:
            raise AttributeValidationError(f"Unknown product spec id {spec_id}")
        schema = spec.characteristic_schema or []

    for field in schema:
        fname = field["name"]
        if field.get("required") and fname not in attributes:
            raise AttributeValidationError(f"Missing required attribute '{fname}'")
        if fname in attributes and field.get("type") == "enum":
            allowed = field.get("values", [])
            if attributes[fname] not in allowed:
                raise AttributeValidationError(
                    f"Invalid value '{attributes[fname]}' for '{fname}', allowed: {allowed}"
                )
    return attributes


def seed_default_catalog_if_empty():
    """
    Additive seed: only inserts sample products if the catalog is currently
    empty (fresh DB). Never overwrites/removes anything that already exists.
    """
    with get_session() as session:
        if session.query(ProductSpecification).count() > 0:
            return  # catalog already has data - do nothing, stay additive

    mobile_spec = create_product_spec(
        name="Postpaid Mobile Plan", category="Mobile",
        characteristic_schema=[
            {"name": "DataAllowanceGB", "type": "number", "required": True},
            {"name": "SIMType", "type": "enum", "values": ["physical", "eSIM"], "required": True},
            {"name": "APN", "type": "string", "required": False},
        ],
    )
    broadband_spec = create_product_spec(
        name="Home Broadband Plan", category="Broadband",
        characteristic_schema=[
            {"name": "SpeedMbps", "type": "number", "required": True},
            {"name": "DataCapGB", "type": "number", "required": False},
            {"name": "ConnectionType", "type": "enum", "values": ["FTTH", "DSL"], "required": True},
        ],
    )
    iot_spec = create_product_spec(
        name="IoT Connectivity Plan", category="IoT",
        characteristic_schema=[
            {"name": "DataAllowanceMB", "type": "number", "required": True},
            {"name": "DeviceType", "type": "string", "required": False},
        ],
    )

    create_offering(name="5G Postpaid 50GB", spec_id=mobile_spec["spec_id"], price=599)
    create_offering(name="4G Postpaid 20GB", spec_id=mobile_spec["spec_id"], price=349)
    create_offering(name="FTTH 200Mbps Home", spec_id=broadband_spec["spec_id"], price=999)
    create_offering(name="IoT Tracker 500MB", spec_id=iot_spec["spec_id"], price=99)