import yaml

VALID_ACTIONS = {
    "create_customer", "place_order", "provision_service",
    "generate_usage", "raise_invoice", "raise_alarm",
    "create_ticket", "mark_invoice_overdue",
}


class SpecValidationError(Exception):
    pass


def parse_spec(spec_text_or_path: str, is_path: bool = True) -> dict:
    if is_path:
        with open(spec_text_or_path) as f:
            spec = yaml.safe_load(f)
    else:
        spec = yaml.safe_load(spec_text_or_path)

    if not spec or "steps" not in spec:
        raise SpecValidationError("Spec must have a top-level 'steps' list")

    for i, step in enumerate(spec["steps"]):
        action = step.get("action")
        if action not in VALID_ACTIONS:
            raise SpecValidationError(
                f"Step {i}: unknown action '{action}'. Valid actions: {sorted(VALID_ACTIONS)}"
            )

    _validate_offering_attributes(spec)
    return spec


def _validate_offering_attributes(spec: dict):
    """
    Checks every place_order step's product attributes against the real
    catalog schema BEFORE the scenario runs, so a missing required
    attribute (e.g. 'ConnectionType' for a Broadband offering) is caught
    at Validate time with a clear message - not mid-run after some
    customers/orders have already been created.
    """
    from modules.catalog import service as catalog_service

    errors = []
    for i, step in enumerate(spec["steps"]):
        if step.get("action") != "place_order":
            continue
        order_spec = step.get("order", {})
        for product in order_spec.get("products", []):
            name = product.get("offering_name")
            if not name:
                errors.append(f"Step {i}: product entry is missing 'offering_name'")
                continue
            offering = catalog_service.get_offering_by_name(name)
            if not offering:
                errors.append(f"Step {i}: unknown offering '{name}' — check the catalog for the exact name")
                continue
            provided = product.get("attributes", {})
            for field in offering.get("characteristic_schema", []):
                if field.get("required") and field["name"] not in provided:
                    errors.append(
                        f"Step {i}: offering '{name}' is missing required attribute "
                        f"'{field['name']}' (type: {field.get('type')}"
                        + (f", allowed values: {field.get('values')}" if field.get("type") == "enum" else "")
                        + ")"
                    )
    if errors:
        raise SpecValidationError("Attribute validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def summarize_plan(spec: dict) -> str:
    """Human-readable summary shown to the user before they click Run (Section 7 UI flow)."""
    lines = [f"Scenario: {spec.get('scenario', 'Unnamed scenario')}"]
    for step in spec["steps"]:
        action = step["action"]
        count = step.get("count", 1)
        for_each = step.get("for_each")
        if for_each:
            lines.append(f"  - {action}: {count} per {for_each}")
        else:
            lines.append(f"  - {action}: {count}")
    return "\n".join(lines)