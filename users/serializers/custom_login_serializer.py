from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers

from users.serializers.bounds import max_length
from users.utils.session_merger import merge_anonymous_session


class CustomLoginSerializer(LoginSerializer):
    """`POST /api/auth/login/`.

    dj_rest_auth declares `username`, `email` and `password` with no maximum
    on any of them, on an endpoint that is unauthenticated and runs the
    password hasher over whatever it is handed. The three overrides below are
    the same fields with the shared ceilings applied -- `email` because an
    address here is an account name, `password` because it is hasher input,
    and `username` because it is the same identifier under dj_rest_auth's
    other spelling (`USERNAME_FIELD` is `email` for this project's user).

    `required`/`allow_blank`/`style` are restated exactly as the library
    declares them: this narrows the bound and nothing else.
    """

    anonymous_id = serializers.UUIDField(required=False, allow_null=True)
    username = serializers.CharField(
        required=False, allow_blank=True, max_length=max_length('email')
    )
    email = serializers.EmailField(
        required=False, allow_blank=True, max_length=max_length('email')
    )
    password = serializers.CharField(
        style={'input_type': 'password'}, max_length=max_length('password')
    )

    def validate(self, attrs):
        anonymous_id = self.initial_data.get('anonymous_id')
        attrs = super().validate(attrs)
        user = attrs.get('user')

        if user and anonymous_id:
            merge_anonymous_session(user, anonymous_id)

        return attrs
