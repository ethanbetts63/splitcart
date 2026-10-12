"""The two ways into an account, as request bodies.

Sessions themselves are `freetheplatform.auth`'s: cookies, rotation, lockout,
revocation. What is splitcart's is the anonymous cart a browser filled before it
had an account, which both doors carry in as `anonymous_id`, and registration,
which the package does not offer.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from freetheplatform.security import bounds
from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    """Checked before the package's `LoginView` sees the body.

    The package hands the password to simplejwt, whose field has no maximum, and
    hashing is deliberately expensive; the bound stops a caller handing it ten
    megabytes. `anonymous_id` is validated here so the merge is given the
    canonical `uuid.UUID` -- registration does the same, so an upper-case
    spelling finds the cart at either door.
    """

    email = bounds.email()
    password = bounds.password()
    anonymous_id = serializers.UUIDField(required=False, allow_null=True)


class RegisterSerializer(serializers.Serializer):
    email = bounds.email()
    # The column is 255; `name` is the rule, and the column only has to be wide
    # enough for it.
    full_name = bounds.char("name")
    password1 = bounds.password()
    password2 = bounds.password()
    #: The signed-out browser's identifier, so the cart it filled follows it
    #: into the new account.
    anonymous_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_email(self, email):
        """Refuse an address that already has an account.

        `iexact`, because MySQL's collation is case-insensitive and two
        addresses differing only in case collide on the unique column anyway --
        as a 500, without this.
        """
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user is already registered with this e-mail address."
            )
        return get_user_model().objects.normalize_email(email)

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": ["The two passwords do not match."]})
        candidate = get_user_model()(email=attrs["email"], full_name=attrs["full_name"])
        try:
            validate_password(attrs["password1"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password1": list(error.messages)})
        return attrs

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            email=validated_data["email"],
            password=validated_data["password1"],
            full_name=validated_data["full_name"],
        )
