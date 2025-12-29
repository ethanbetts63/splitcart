from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers
from users.utils.session_merger import merge_anonymous_session

class CustomLoginSerializer(LoginSerializer):
    anonymous_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        anonymous_id = self.initial_data.get('anonymous_id')
        attrs = super().validate(attrs)
        user = attrs.get('user')

        if user and anonymous_id:
            merge_anonymous_session(user, anonymous_id)

        return attrs
