from django.db import models

class StoreGroup(models.Model):
    """
    Represents a geographic cluster of stores belonging to a single company.
    """
    name = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='store_groups')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class StoreGroupMembership(models.Model):
    """
    Links a Store to a StoreGroup, signifying its membership.
    Also tracks metadata about the membership, like its role as an ambassador.
    """
    store = models.OneToOneField('companies.Store', on_delete=models.CASCADE, related_name='group_membership')
    group = models.ForeignKey(StoreGroup, on_delete=models.CASCADE, related_name='memberships')
    last_scraped_as_ambassador = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('store', 'group')

    def __str__(self):
        return f'{self.store.store_name} in {self.group.name}'
