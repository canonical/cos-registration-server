from api.serializer import DeviceSerializer
from devices.models import Device
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser


def devices(request):
    if request.method == "GET":
        devices = Device.objects.all()
        serialized = DeviceSerializer(devices, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(data=data)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)


def device(request, uid):
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
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == "DELETE":
        device.delete()
        return HttpResponse(status=204)
