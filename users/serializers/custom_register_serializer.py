from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.serializers.bounds import max_length
from users.utils.session_merger import merge_anonymous_session

# Ceilings by kind, not by number. `bounds.py` says why the table is mirrored
# here rather than imported from the shared package, and what each kind is for:
# a password bound is what the hasher may be asked to chew through, an email
# bound sits below the width every site here truncates an address into, and a
# person's name is a `name` -- not the 255 the column happens to be wide.
PASSWORD_MAX_LENGTH = max_length("password")
EMAIL_MAX_LENGTH = max_length("email")
# `users.User.full_name`'s column is 255, so this is tighter than the write can
# fail at. The kind is the rule; the column only has to be wide enough for it.
FULL_NAME_MAX_LENGTH = max_length("name")


class CustomRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(max_length=FULL_NAME_MAX_LENGTH)
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)
    password1 = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)
    password2 = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)
    #: The signed-out browser's identifier, so the cart it filled follows it
    #: into the new account. See `save()`.
    anonymous_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

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
        """Create the account, then hand it the cart the browser already had.

        Logging in has always done this -- `CustomLoginSerializer.validate()`
        calls the same merger -- but registration went through dj-rest-auth's
        own serializer, which takes no `anonymous_id` and never calls login. A
        shopper who filled a cart signed out and then created an account lost
        it, while the same shopper signing in kept it. That asymmetry was the
        whole defect; the merge itself was never wrong, and is pinned
        independently in `users/tests/util_tests/test_session_merger.py`.

        `merge_anonymous_session` is a no-op when the id is absent or names no
        active cart, so this is safe on every ordinary registration.
        """
        user = super().save(request)
        user.full_name = self.cleaned_data.get('full_name')
        user.save()
        merge_anonymous_session(user, self.validated_data.get('anonymous_id'))
        return user
