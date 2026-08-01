from faker import Faker

fake = Faker()

TEMPLATES = {
    "individual_prepaid_customer": {"customer_type": "individual", "segment": "consumer"},
    "individual_postpaid_customer": {"customer_type": "individual", "segment": "consumer"},
    "sme_enterprise_customer": {"customer_type": "organization", "segment": "sme"},
}


def generate_customer_payload(template: str = "individual_prepaid_customer") -> dict:
    base = TEMPLATES.get(template, TEMPLATES["individual_prepaid_customer"])
    if base["customer_type"] == "organization":
        name = fake.company()
    else:
        name = fake.name()
    return {
        "name": name,
        "customer_type": base["customer_type"],
        "segment": base["segment"],
        "email": fake.unique.email(),
        "phone": fake.phone_number(),
        "address": fake.address().replace("\n", ", "),
    }
