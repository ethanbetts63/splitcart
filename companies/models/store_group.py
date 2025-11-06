from django.db import models

class StoreGroup(models.Model):
    """
    Represents a geographic or logical cluster of stores belonging to a single company.
    """
    STATUS_CHOICES = [
        ('HEALTHY', 'Healthy'),
        ('DIVERGENCE_DETECTED', 'Divergence Detected'),
    ]

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='store_groups')
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='HEALTHY')

    # The current source of truth for the group's pricing
    anchor = models.ForeignKey(
        'companies.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anchor_for_group'
    )



    def __str__(self):
        return f"{self.company.name} Group {self.id}"
