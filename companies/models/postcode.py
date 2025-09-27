from django.db import models

class Postcode(models.Model):
    postcode = models.CharField(max_length=10, unique=True, db_index=True)
    state = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ['postcode']

    def __str__(self):
        return f"{self.postcode}, {self.state} ({self.latitude}, {self.longitude})"
