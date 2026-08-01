from django.contrib import admin
from django.urls import path
from assurance.views import dashboard

urlpatterns = [
    path("admin/assurance/dashboard/", dashboard, name="assurance-dashboard"),
    path("admin/", admin.site.urls),
]
