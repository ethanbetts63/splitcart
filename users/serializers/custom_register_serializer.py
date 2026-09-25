from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

# What the hasher may be asked to chew through. dj_rest_auth declares password1
# and password2 as plain write-only CharFields with no maximum, on an endpoint
# that by definition accepts unauthenticated callers -- so an unbounded field is
# an unbounded amount of CPU per request. 128 is the shared family ceiling.
PASSWORD_MAX_LENGTH = 128
# Below auth.User.username's 150-character width, which every site here
# truncates an address into. Two addresses agreeing on their first 150
# characters would collide on the unique constraint, and the second person to
# sign up would be told they already have an account with no way forward.
EMAIL_MAX_LENGTH = 150
FULL_NAME_MAX_LENGTH = 255  # users.User.full_name's column width.


class CustomRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(max_length=FULL_NAME_MAX_LENGTH)
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)
    password1 = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)
    password2 = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)

    def validate_email(self, email):
        """Refuse an address that already has an account.

        dj-rest-auth's own check asks `EmailAddress.objects.is_verified(email)`,
        and `ACCOUNT_EMAIL_VERIFICATION` is `'none'` here, so no address is ever
        verified and the check never fires. The INSERT then hit
        `users_user.email`'s unique constraint and the endpoint answered 500 --
        to anyone who had simply forgotten they already had an account, and to
        anyone probing which addresses are registered.

        `ACCOUNT_UNIQUE_EMAIL` is True and the column is unique; this is the
        serializer saying the same thing in time to return a field error.
        `iexact` rather than `exact` because MySQL's collation is
        case-insensitive, so two addresses differing only in case collide in the
        database as well.
        """
        email = super().validate_email(email)
        if email and get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                'A user is already registered with this e-mail address.'
            )
        return email

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['full_name'] = self.validated_data.get('full_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.full_name = self.cleaned_data.get('full_name')
        user.save()
        return user
