"""Device administration registration."""

from django.contrib import admin

from .models import Certificate, Device

admin.site.register(Device)
admin.site.register(Certificate)
