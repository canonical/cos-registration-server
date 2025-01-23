"""Device administration registration."""

from django.contrib import admin

from .models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    PrometheusAlertRule,
    LokiAlertRule,
)


admin.site.register(FoxgloveDashboard)
admin.site.register(GrafanaDashboard)
admin.site.register(PrometheusAlertRule)
admin.site.register(LokiAlertRule)
