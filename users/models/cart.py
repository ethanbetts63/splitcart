import uuid
from django.db import models
from django.conf import settings
from users.models.selected_store_list import SelectedStoreList

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    anonymous_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, default="Unnamed Cart")
    is_active = models.BooleanField(default=False)
    selected_store_list = models.ForeignKey(
        SelectedStoreList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_user_cart_name'),
            models.UniqueConstraint(fields=['user'], condition=models.Q(is_active=True, user__isnull=False), name='unique_active_user_cart'),
            models.UniqueConstraint(fields=['anonymous_id'], condition=models.Q(is_active=True, anonymous_id__isnull=False), name='unique_active_anonymous_cart'),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email if self.user else 'Anonymous'})"
