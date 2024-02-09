"""API urls."""
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # make a version API url
    path("v1/devices", views.devices, name="devices"),
    path("v1/devices/<str:uid>", views.device, name="device"),
]
