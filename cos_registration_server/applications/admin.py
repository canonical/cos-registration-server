"""Device administration registration."""

from django.contrib import admin

from .models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRule,
    PrometheusAlertRule,
)

admin.site.register(FoxgloveDashboard)
admin.site.register(GrafanaDashboard)
admin.site.register(PrometheusAlertRule)
admin.site.register(LokiAlertRule)
