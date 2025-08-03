from django.db import models

class Company(models.Model):
    """
    Represents a parent company or brand that owns one or more stores.
    e.g., 'IGA', 'Coles Group'.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the parent company."
    )

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name
