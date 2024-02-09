from devices.models import Device
from rest_framework import serializers


class DeviceSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    creation_date = serializers.DateTimeField(read_only=True)
    address = serializers.IPAddressField(required=True)

    def create(self, validated_data):
        return Device.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.address = validated_data.get("address", instance.address)
        instance.save()
        return instance
