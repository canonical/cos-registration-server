"""Device administration registration."""

from django.contrib import admin

from .models import FoxgloveDashboard, GrafanaDashboard

admin.site.register(FoxgloveDashboard)
admin.site.register(GrafanaDashboard)
