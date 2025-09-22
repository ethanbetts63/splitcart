from django.db import models

class StoreGroup(models.Model):
    """
    Represents a geographic or logical cluster of stores belonging to a single company.
    """
    name = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='store_groups')
    is_active = models.BooleanField(default=True)

    # The current source of truth for the group's pricing
    ambassador = models.ForeignKey(
        'companies.Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ambassador_for_group'
    )

    # A temporary list of recently scraped stores to be checked
    candidates = models.ManyToManyField(
        'companies.Store',
        related_name='candidate_for_groups',
        blank=True
    )

    def __str__(self):
        return self.name

