"""Simulates OSS network activity: usage collection + occasional faults.

Run once for a single tick:
    python manage.py simulate_network_events

Run continuously (every N seconds) for a live demo:
    python manage.py simulate_network_events --loop --interval 10
"""
import time
from django.core.management.base import BaseCommand
from service_inventory.models import Service
from usage.services import generate_usage_for_service
from fault_mgmt.services import maybe_raise_random_fault


class Command(BaseCommand):
    help = "Simulates usage collection and fault events for active services."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Run continuously")
        parser.add_argument("--interval", type=int, default=10, help="Seconds between ticks when looping")

    def handle(self, *args, **options):
        if options["loop"]:
            self.stdout.write(self.style.SUCCESS("Starting continuous simulation. Ctrl+C to stop."))
            try:
                while True:
                    self.tick()
                    time.sleep(options["interval"])
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("Simulation stopped."))
        else:
            self.tick()

    def tick(self):
        active_services = Service.objects.filter(status="ACTIVE")
        usage_count = 0
        for service in active_services:
            generate_usage_for_service(service)
            usage_count += 1

        fault = maybe_raise_random_fault(probability=0.3)
        msg = f"Generated usage for {usage_count} active service(s)."
        if fault:
            msg += f" Raised fault: {fault}"
        self.stdout.write(self.style.SUCCESS(msg))
