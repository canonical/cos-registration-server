"""API views."""
import json

from api.serializer import DeviceSerializer
from devices.models import Device
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser

from .dashboards import add_dashboards, delete_dashboards


def devices(request):
    """Devices API view.

    request: Http request (GET,POST).
    return: Http JSON response.
    """
    if request.method == "GET":
        devices = Device.objects.all().values(
            "uid", "creation_date", "address", "public_ssh_key"
        )
        serialized = DeviceSerializer(devices, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(data=data)
        if serialized.is_valid():
            serialized.save()
            add_dashboards(serialized.instance)
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)


def device(request, uid):
    """Device API view.

    request: Http request (GET,PACH, DELETE).
    uid: Device UID passed in the URL.
    return: Http JSON response.
    """
    try:
        device = Device.objects.get(uid=uid)
    except Device.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serialized = DeviceSerializer(device)
        return JsonResponse(serialized.data)
    if request.method == "PATCH":
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(device, data=data, partial=True)
        if serialized.is_valid():
            serialized.save()
            delete_dashboards(serialized.instance)
            add_dashboards(serialized.instance)
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == "DELETE":
        device.delete()
        delete_dashboards(device)
        return HttpResponse(status=204)


def foxglove_layout(request, uid, layout_uid):
    """Foxglove layout json file API.

    request: Http request (GET).
    uid: Device UID passed in the URL.
    layout_uid: Foxglove layout uid.
    return: Http JSON file response.
    """
    if request.method == "GET":
        try:
            device = Device.objects.get(uid=uid)
        except Device.DoesNotExist:
            return HttpResponse(status=404)
        if (layout := device.foxglove_layouts.get(layout_uid)) is None:
            return HttpResponse(status=404)
        response = HttpResponse(
            json.dumps(layout), content_type="application/json"
        )
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{layout_uid}.json"'
        return response
