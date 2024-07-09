from django.db import models

class Route(models.Model):
    name = models.CharField(max_length=100)
    # Agrega otros campos según sea necesario

class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    # Agrega otros campos según sea necesario