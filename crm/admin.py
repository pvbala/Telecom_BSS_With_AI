from django.contrib import admin
from .models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("customer", "channel", "summary", "created_at")
    list_filter = ("channel",)
    search_fields = ("customer__name", "summary")
