"""
Converts a plain-English Business Process Test Case description (e.g.
"Create 5 Customers, Put 2 Orders for each of these 5 customers,
provision the service, raise the invoice") into a structured YAML spec
that test_data_engine.spec_parser / orchestrator can execute.

Uses the same llm.client.generate() Gemini->Grok->Ollama cascade as
everything else - one call site, one fallback policy.
"""
import yaml
from llm.client import generate
from test_data_engine.spec_parser import parse_spec, SpecValidationError

SPEC_SCHEMA_GUIDE = """
Produce ONLY a YAML document (no markdown fences, no explanation) with this shape:

scenario: "<short title>"
steps:
  - action: create_customer
    count: <int>
    template: individual_prepaid_customer   # or individual_postpaid_customer, sme_enterprise_customer

  - action: place_order
    count: <int>                  # orders PER customer created above
    order:
      channel: online
      products:
        - offering_name: "5G Postpaid 50GB"   # must match an existing catalog offering name
          attributes: { DataAllowanceGB: 50, SIMType: eSIM, APN: internet.mno }

  - action: provision_service     # provisions every order placed above

  - action: generate_usage        # generates usage for every provisioned product instance
    profile: moderate_data_user   # or light_user, heavy_user
    duration_days: 30

  - action: raise_invoice         # raises one invoice per account, summing usage charges

  - action: raise_alarm           # optional: only include if the request mentions alarms/faults
    count: <int>
    severities: [minor, major, critical]

Only include the steps the user's request actually implies, in the
correct logical order (customers -> orders -> provisioning -> usage -> invoice).

Available catalog offerings and their attribute requirements - you MUST
include every "requires" attribute listed for whichever offering(s) you use:
__OFFERINGS__
"""


def _describe_offerings() -> str:
    """
    Builds a description of every catalog offering INCLUDING its required
    attributes, e.g.:
      - "FTTH 200Mbps Home": requires SpeedMbps (number), ConnectionType (enum: FTTH, DSL); optional DataCapGB (number)
    Feeding the LLM the actual schema (not just offering names) is what
    prevents it from generating orders that omit a required attribute
    for anything other than the one example baked into the guide below.
    """
    from modules.catalog.service import list_offerings
    lines = []
    for o in list_offerings():
        from modules.catalog.service import get_offering_by_id
        full = get_offering_by_id(o["id"])
        schema = full["characteristic_schema"] if full else []
        required = [f for f in schema if f.get("required")]
        optional = [f for f in schema if not f.get("required")]

        def _fmt(f):
            if f.get("type") == "enum":
                return f"{f['name']} (enum: {', '.join(f.get('values', []))})"
            return f"{f['name']} ({f.get('type')})"

        parts = []
        if required:
            parts.append("requires " + ", ".join(_fmt(f) for f in required))
        if optional:
            parts.append("optional " + ", ".join(_fmt(f) for f in optional))
        lines.append(f'  - "{o["name"]}": ' + ("; ".join(parts) if parts else "no attributes"))
    return "\n".join(lines)


def translate(nl_text: str) -> dict:
    offerings_description = _describe_offerings()

    # NOTE: we deliberately use a plain string replace (not str.format) here,
    # because the schema guide above contains literal YAML examples with
    # curly braces (e.g. { DataAllowanceGB: 50, ... }) which str.format()
    # would misinterpret as format placeholders and raise a KeyError.
    schema_guide = SPEC_SCHEMA_GUIDE.replace("__OFFERINGS__", offerings_description)

    prompt = (
        f"{schema_guide}\n\n"
        f"User's request: \"{nl_text}\"\n\nYAML:"
    )
    llm_result = generate(prompt)
    raw_yaml = llm_result["text"].strip()
    # strip markdown fences if the model added them anyway
    raw_yaml = raw_yaml.strip("`")
    if raw_yaml.lower().startswith("yaml"):
        raw_yaml = raw_yaml[4:].strip()

    try:
        parsed = yaml.safe_load(raw_yaml)
        parse_spec(raw_yaml, is_path=False)  # validate against known actions
    except (yaml.YAMLError, SpecValidationError) as e:
        return {"error": f"Could not produce a valid spec: {e}", "raw_yaml": raw_yaml,
                "provider_used": llm_result["provider_used"]}

    return {"yaml": raw_yaml, "parsed": parsed, "provider_used": llm_result["provider_used"]}