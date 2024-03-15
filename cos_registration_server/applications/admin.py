"""Device administration registration."""

from django.contrib import admin

from .models import GrafanaDashboard

admin.site.register(GrafanaDashboard)
