from django.contrib.auth.models import BaseUserManager
from allauth.account.models import EmailAddress

class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(email, password, **extra_fields)

        # Mark the superuser's email as verified
        try:
            email_address = EmailAddress.objects.get(user=user, email=user.email)
            email_address.verified = True
            email_address.save()
        except EmailAddress.DoesNotExist:
            EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)

        return user