from django.db import models


class Device(models.Model):
    uid = models.CharField(max_length=200)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")

    def __str__(self):
        return self.uid
