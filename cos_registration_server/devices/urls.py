from django.urls import path

from . import views

app_name = "devices"

urlpatterns = [
    path("", views.devices.as_view(), name="devices"),
    path("<str:uid>", views.device, name="device"),
]
