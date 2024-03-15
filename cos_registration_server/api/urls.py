"""API urls."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # make a version API url
    path("v1/devices", views.devices, name="devices"),
    path("v1/devices/<str:uid>", views.device, name="device"),
    path(
        "v1/applications/grafana/dashboards",
        views.grafana_dashboards,
        name="grafana_dashboards",
    ),
    path(
        "v1/applications/grafana/dashboards/<str:uid>",
        views.grafana_dashboard,
        name="grafana_dashboard",
    ),
]
