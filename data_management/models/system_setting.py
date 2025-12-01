from django.db import models

class SystemSetting(models.Model):
    """
    A key-value store for system-wide settings that can be configured
    at runtime or by management commands.
    """
    key = models.CharField(max_length=100, primary_key=True)
    value = models.JSONField()

    def __str__(self):
        return self.key
