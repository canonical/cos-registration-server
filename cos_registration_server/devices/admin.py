"""Device administration registration."""

from django.contrib import admin

from .models import Device, DeviceCertificate

admin.site.register(Device)
admin.site.register(DeviceCertificate)
