from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from service_inventory.models import Service
from fault_mgmt.models import Fault
from tickets.models import Ticket


@staff_member_required
def dashboard(request):
    services_by_status = Service.objects.values("status").annotate(count=Count("id"))
    open_faults = Fault.objects.exclude(status="RESOLVED").select_related("resource").order_by("-detected_at")[:20]
    open_tickets = Ticket.objects.exclude(status__in=["RESOLVED", "CLOSED"]).select_related("customer").order_by("-created_at")[:20]

    context = {
        "services_by_status": services_by_status,
        "open_faults": open_faults,
        "open_tickets": open_tickets,
        "open_fault_count": Fault.objects.exclude(status="RESOLVED").count(),
        "open_ticket_count": Ticket.objects.exclude(status__in=["RESOLVED", "CLOSED"]).count(),
        "active_service_count": Service.objects.filter(status="ACTIVE").count(),
    }
    return render(request, "assurance/dashboard.html", context)
