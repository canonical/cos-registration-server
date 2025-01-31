"""Device administration registration."""

from django.contrib import admin

from .models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
)

admin.site.register(FoxgloveDashboard)
admin.site.register(GrafanaDashboard)
admin.site.register(PrometheusAlertRuleFile)
admin.site.register(LokiAlertRuleFile)
