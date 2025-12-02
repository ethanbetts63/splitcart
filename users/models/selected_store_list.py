import uuid
from django.db import models
from django.conf import settings
from companies.models import Store

class SelectedStoreList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='store_lists'
    )
    anonymous_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, default="My Store List")
    is_user_defined = models.BooleanField(default=False)
    stores = models.ManyToManyField(Store, related_name='store_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(auto_now_add=True) # Added this field

    class Meta:
        verbose_name = "Selected Store List"
        verbose_name_plural = "Selected Store Lists"
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} ({self.user.email if self.user else 'Anonymous'})"
