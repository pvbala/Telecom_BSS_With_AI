import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from modules.party import service as party_service
from modules.catalog import service as catalog_service
from modules.order import service as order_service
from modules.inventory import service as inventory_service
from modules.mediation_rating import service as mediation_service
from modules.billing import service as billing_service
from modules.assurance import service as assurance_service

st.set_page_config(page_title="Manage Entities", layout="wide")
st.title("🛠️ Manage Entities")
st.caption("Create BSS/OSS records directly — an alternative to the Test Data Generator "
           "for one-off, manually specified data.")

tabs = st.tabs([
    "👤 Customer & Account", "📦 Product Catalog", "🧾 Place Order",
    "🔌 Provision Order", "📶 Usage & Invoice", "🚨 Assurance",
])

# ---------------------------------------------------------------------
# TAB 1 — Party: Customer & Account
# ---------------------------------------------------------------------
with tabs[0]:
    st.subheader("Create a Customer")
    with st.form("create_customer_form"):
        name = st.text_input("Name")
        customer_type = st.selectbox("Customer type", ["individual", "organization"])
        segment = st.selectbox("Segment", ["consumer", "sme", "enterprise"])
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_input("Address")
        submitted = st.form_submit_button("Create Customer")
        if submitted:
            if not name:
                st.error("Name is required.")
            else:
                result = party_service.create_customer(
                    name=name, customer_type=customer_type, segment=segment,
                    email=email or None, phone=phone or None, address=address or None,
                )
                st.success(f"Created {result['customer_code']} (customer_id={result['customer_id']}), "
                           f"account {result['account_code']} (account_id={result['account_id']})")

    st.divider()
    st.subheader("Existing customers")
    st.dataframe(party_service.list_customers(limit=200), use_container_width=True)


# ---------------------------------------------------------------------
# TAB 2 — Catalog: Product Specification + Product Offering
# ---------------------------------------------------------------------
with tabs[1]:
    st.subheader("Create a Product Specification (defines the attribute schema)")

    if "attr_rows" not in st.session_state:
        st.session_state.attr_rows = [{"name": "", "type": "string", "required": True, "values": ""}]

    with st.form("create_spec_form"):
        spec_name = st.text_input("Specification name", placeholder="e.g. Enterprise WAN Link")
        spec_category = st.text_input("Category", placeholder="e.g. Enterprise, Mobile, Broadband, IoT")

        st.markdown("**Characteristics (attribute schema)**")
        for i, row in enumerate(st.session_state.attr_rows):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
            row["name"] = c1.text_input(f"Attribute name #{i+1}", value=row["name"], key=f"an_{i}")
            row["type"] = c2.selectbox(f"Type #{i+1}", ["string", "number", "enum"],
                                        index=["string", "number", "enum"].index(row["type"]), key=f"at_{i}")
            row["required"] = c3.checkbox(f"Required #{i+1}", value=row["required"], key=f"ar_{i}")
            if row["type"] == "enum":
                row["values"] = c4.text_input(f"Allowed values (comma-sep) #{i+1}", value=row["values"], key=f"av_{i}")

        add_col, submit_col = st.columns([1, 3])
        add_attr = add_col.form_submit_button("+ Add attribute row")
        submitted_spec = submit_col.form_submit_button("Create Product Specification", type="primary")

        if add_attr:
            st.session_state.attr_rows.append(
                {"name": "", "type": "string", "required": True, "values": ""})
            st.rerun()

        if submitted_spec:
            schema = []
            for row in st.session_state.attr_rows:
                if not row["name"]:
                    continue
                field = {"name": row["name"], "type": row["type"], "required": row["required"]}
                if row["type"] == "enum" and row["values"]:
                    field["values"] = [v.strip() for v in row["values"].split(",") if v.strip()]
                schema.append(field)

            if not spec_name or not schema:
                st.error("Specification name and at least one named attribute are required.")
            else:
                result = catalog_service.create_product_spec(
                    name=spec_name, category=spec_category or "General", characteristic_schema=schema,
                )
                st.success(f"Created {result['spec_code']} — {result['name']} (spec_id={result['spec_id']})")
                st.session_state.attr_rows = [{"name": "", "type": "string", "required": True, "values": ""}]

    st.divider()
    st.subheader("Create a Product Offering (the sellable, priced wrapper)")
    specs = catalog_service.list_product_specs()
    if not specs:
        st.info("Create a Product Specification above first.")
    else:
        with st.form("create_offering_form"):
            spec_choice = st.selectbox(
                "Product Specification", specs,
                format_func=lambda s: f"{s['name']} ({s['category']}) — id={s['id']}",
            )
            offering_name = st.text_input("Offering name", placeholder="e.g. Enterprise WAN 1Gbps Gold")
            price = st.number_input("Price", min_value=0.0, step=1.0)
            currency = st.selectbox("Currency", ["INR", "USD", "EUR"])
            billing_frequency = st.selectbox("Billing frequency", ["monthly", "one_time", "usage_based"])
            submitted_offering = st.form_submit_button("Create Offering", type="primary")

            if submitted_offering:
                if not offering_name:
                    st.error("Offering name is required.")
                else:
                    result = catalog_service.create_offering(
                        name=offering_name, spec_id=spec_choice["id"], price=price,
                        currency=currency, billing_frequency=billing_frequency,
                    )
                    st.success(f"Created {result['offering_code']} — {result['name']}")

    st.divider()
    st.subheader("Existing offerings")
    st.dataframe(catalog_service.list_offerings(), use_container_width=True)


# ---------------------------------------------------------------------
# TAB 3 — Order: Place Order (with dynamic attribute form from the spec)
# ---------------------------------------------------------------------
with tabs[2]:
    st.subheader("Place an Order")
    customers = party_service.list_customers(limit=500)
    offerings = catalog_service.list_offerings()

    if not customers:
        st.info("Create a customer first (Customer & Account tab).")
    elif not offerings:
        st.info("Create a product offering first (Product Catalog tab).")
    else:
        customer_choice = st.selectbox(
            "Customer", customers, format_func=lambda c: f"{c['code']} — {c['name']} (id={c['id']})",
        )
        offering_choice = st.selectbox(
            "Offering", offerings, format_func=lambda o: f"{o['code']} — {o['name']} (₹{o['price']})",
        )

        # Dynamic attribute form driven by the offering's ProductSpecification schema
        # (this is the flexible product model in action - the form has no
        # hard-coded fields, it renders whatever the spec declares)
        full_offering = catalog_service.get_offering_by_id(offering_choice["id"])
        schema = full_offering["characteristic_schema"] if full_offering else []

        attributes = {}
        if schema:
            st.markdown("**Product attributes** (defined by this offering's specification)")
            for field in schema:
                fname = field["name"]
                label = f"{fname}{' *' if field.get('required') else ''}"
                if field.get("type") == "number":
                    attributes[fname] = st.number_input(label, key=f"order_attr_{fname}")
                elif field.get("type") == "enum":
                    attributes[fname] = st.selectbox(label, field.get("values", []), key=f"order_attr_{fname}")
                else:
                    attributes[fname] = st.text_input(label, key=f"order_attr_{fname}")

        channel = st.selectbox("Channel", ["online", "retail_store", "call_center", "partner"])

        if st.button("Place Order", type="primary"):
            account = party_service.get_account_for_customer(customer_choice["id"])
            try:
                result = order_service.place_order(
                    customer_id=customer_choice["id"],
                    account_id=account["id"],
                    items=[{"offering_id": offering_choice["id"], "attributes": attributes}],
                    channel=channel,
                )
                st.success(f"Order {result['order_code']} placed (status: {result['status']}). "
                           f"Go to 'Provision Order' tab to activate it.")
            except Exception as e:
                st.error(f"Could not place order: {e}")

    st.divider()
    st.subheader("Existing orders")
    st.dataframe(order_service.list_orders(limit=200), use_container_width=True)


# ---------------------------------------------------------------------
# TAB 4 — Provisioning: activate a CREATED order
# ---------------------------------------------------------------------
with tabs[3]:
    st.subheader("Provision / Activate an Order")
    all_orders = order_service.list_orders(limit=500)
    pending_orders = [o for o in all_orders if o["status"] != "ACTIVE"]

    if not pending_orders:
        st.info("No pending orders — every order is already provisioned/active.")
    else:
        order_choice = st.selectbox(
            "Order awaiting provisioning", pending_orders,
            format_func=lambda o: f"{o['code']} — status={o['status']} (customer_id={o['customer_id']})",
        )
        if st.button("🔌 Provision this order", type="primary"):
            try:
                result = order_service.provision_order(order_choice["id"])
                st.success(f"Order {order_choice['code']} provisioned — "
                           f"{len(result['product_instances'])} product instance(s) created and activated.")
                st.json(result)
            except Exception as e:
                st.error(f"Provisioning failed: {e}")

    st.divider()
    st.subheader("Existing product instances")
    st.dataframe(inventory_service.list_product_instances(), use_container_width=True)


# ---------------------------------------------------------------------
# TAB 5 — Usage generation + manual Invoice raising
# ---------------------------------------------------------------------
with tabs[4]:
    st.subheader("Generate Usage for a Product Instance")
    instances = inventory_service.list_product_instances()
    active_instances = [p for p in instances if p["status"] == "active"]

    if not active_instances:
        st.info("No active product instances yet — provision an order first.")
    else:
        pi_choice = st.selectbox(
            "Product instance", active_instances,
            format_func=lambda p: f"{p['code']} (customer_id={p['customer_id']})",
        )
        profile = st.selectbox("Usage profile", ["light_user", "moderate_data_user", "heavy_user"])
        duration_days = st.slider("Duration (days)", 1, 90, 30)
        if st.button("Generate usage", type="primary"):
            result = mediation_service.generate_usage(
                product_instance_id=pi_choice["id"], profile=profile, duration_days=duration_days,
            )
            st.success(f"Generated {result['records_created']} usage record(s), "
                       f"total charge ₹{result['total_amount']}")

    st.divider()
    st.subheader("Raise an Invoice for an Account")
    customers = party_service.list_customers(limit=500)
    if not customers:
        st.info("No customers yet.")
    else:
        cust_choice = st.selectbox(
            "Customer", customers, format_func=lambda c: f"{c['code']} — {c['name']}", key="invoice_customer",
        )
        account = party_service.get_account_for_customer(cust_choice["id"])
        if account:
            st.caption(f"Account: {account['code']} (account_id={account['id']})")
            if st.button("🧾 Raise invoice (sums all rated usage for this customer)", type="primary"):
                result = billing_service.raise_invoice_for_account(account["id"])
                st.success(f"Invoice {result['invoice_code']} raised for ₹{result['amount']} "
                           f"(status: {result['status']})")

    st.divider()
    st.subheader("Existing invoices")
    st.dataframe(billing_service.list_invoices(), use_container_width=True)


# ---------------------------------------------------------------------
# TAB 6 — Assurance: Alarm + Trouble Ticket
# ---------------------------------------------------------------------
with tabs[5]:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Raise an Alarm")
        alarm_type = st.selectbox("Alarm type",
                                   ["link_down", "high_latency", "packet_loss", "hardware_fault"])
        severity = st.selectbox("Severity", ["minor", "major", "critical", "warning"])
        description = st.text_area("Description", value="Manually raised alarm", key="alarm_desc")
        if st.button("🚨 Raise alarm", type="primary"):
            result = assurance_service.raise_alarm(
                alarm_type=alarm_type, severity=severity, description=description,
            )
            st.success(f"Alarm {result['code']} raised — anomaly detector will react automatically.")

    with col2:
        st.subheader("Create a Trouble Ticket")
        customers = party_service.list_customers(limit=500)
        if not customers:
            st.info("No customers yet.")
        else:
            ticket_customer = st.selectbox(
                "Customer", customers, format_func=lambda c: f"{c['code']} — {c['name']}", key="ticket_customer",
            )
            subject = st.text_input("Subject", placeholder="e.g. Billing dispute")
            ticket_desc = st.text_area("Description", key="ticket_desc")
            if st.button("🎫 Create ticket", type="primary"):
                if not subject:
                    st.error("Subject is required.")
                else:
                    result = assurance_service.create_ticket(
                        subject=subject, description=ticket_desc,
                        customer_id=ticket_customer["id"],
                    )
                    st.success(f"Ticket {result['code']} created.")

    st.divider()
    c1, c2 = st.columns(2)
    c1.write("Alarms")
    c1.dataframe(assurance_service.list_alarms(), use_container_width=True)
    c2.write("Tickets")
    c2.dataframe(assurance_service.list_tickets(), use_container_width=True)