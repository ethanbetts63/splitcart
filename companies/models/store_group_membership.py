from django.db import models

class StoreGroupMembership(models.Model):
    """
    A simple and pure linking table that connects a Store to a StoreGroup.
    Its existence signifies that a store is part of a group.
    """
    store = models.OneToOneField('companies.Store', on_delete=models.CASCADE, related_name='group_membership')
    group = models.ForeignKey('companies.StoreGroup', on_delete=models.CASCADE, related_name='memberships')

    class Meta:
        unique_together = ('store', 'group')

    def __str__(self):
        return f'{self.store.store_name} in {self.group}'
