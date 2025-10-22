import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from ..managers import UserManager

class User(AbstractUser):
    """
    Custom user model that uses email as the username and has a full_name field.
    """
    # Remove the default username field
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
