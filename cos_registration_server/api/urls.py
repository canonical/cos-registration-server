"""API urls."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # make a version API url
    path("v1/health/", views.HealthView.as_view(), name="health"),
    path("v1/devices/", views.DevicesView.as_view(), name="devices"),
    path("v1/devices/<str:uid>/", views.DeviceView.as_view(), name="device"),
    path(
        "v1/applications/grafana/dashboards/",
        views.GrafanaDashboardsView.as_view(),
        name="grafana_dashboards",
    ),
    path(
        "v1/applications/grafana/dashboards/<str:uid>/",
        views.GrafanaDashboardView.as_view(),
        name="grafana_dashboard",
    ),
    path(
        "v1/applications/foxglove/dashboards/",
        views.FoxgloveDashboardsView.as_view(),
        name="foxglove_dashboards",
    ),
    path(
        "v1/applications/foxglove/dashboards/<str:uid>/",
        views.FoxgloveDashboardView.as_view(),
        name="foxglove_dashboard",
    ),
    path(
        "v1/applications/prometheus/alert_rules/",
        views.PrometheusAlertRulesView.as_view(),
        name="prometheus_alert_rules",
    ),
    path(
        "v1/applications/prometheus/alert_rules/<str:uid>/",
        views.PrometheusAlertRuleView.as_view(),
        name="prometheus_alert_rule",
    ),
]
