from decimal import Decimal
from django.core.management.base import BaseCommand
from catalog.models import Product, PricePlan
from resource_inventory.models import NetworkResource
from comm_inventory.models import StockItem


class Command(BaseCommand):
    help = "Seeds demo products, price plans, and inventory for the two telecom products."

    def handle(self, *args, **options):
        sim, _ = Product.objects.get_or_create(
            name="Mobile Prepaid SIM", product_type="PREPAID_SIM",
            defaults={"description": "Prepaid mobile connection"},
        )
        fiber, _ = Product.objects.get_or_create(
            name="Home Fiber Broadband", product_type="FIBER",
            defaults={"description": "Fiber-to-the-home broadband connection"},
        )

        PricePlan.objects.get_or_create(
            product=sim, name="Value Pack",
            defaults=dict(price=Decimal("199"), validity_days=28, data_per_day_gb=1.0, voice_minutes=100),
        )
        PricePlan.objects.get_or_create(
            product=sim, name="Power Pack",
            defaults=dict(price=Decimal("399"), validity_days=56, data_per_day_gb=2.0, voice_minutes=1000),
        )
        PricePlan.objects.get_or_create(
            product=fiber, name="Home 100",
            defaults=dict(price=Decimal("999"), speed_mbps=100, monthly_data_cap_gb=None),
        )
        PricePlan.objects.get_or_create(
            product=fiber, name="Home 300",
            defaults=dict(price=Decimal("1499"), speed_mbps=300, monthly_data_cap_gb=None),
        )

        for i in range(1, 21):
            NetworkResource.objects.get_or_create(
                resource_type="MSISDN", identifier=f"9198765{43000 + i}",
            )
        for i in range(1, 11):
            NetworkResource.objects.get_or_create(
                resource_type="FIBER_PORT", identifier=f"ONT-{1000 + i}",
            )

        StockItem.objects.get_or_create(
            product=sim, item_type="SIM_CARD", batch_reference="BATCH-SIM-001",
            defaults={"quantity_on_hand": 500},
        )
        StockItem.objects.get_or_create(
            product=fiber, item_type="ONT_DEVICE", batch_reference="BATCH-ONT-001",
            defaults={"quantity_on_hand": 100},
        )

        self.stdout.write(self.style.SUCCESS(
            "Seeded: 2 products, 4 price plans, 20 MSISDNs, 10 fiber ports, stock items."
        ))
