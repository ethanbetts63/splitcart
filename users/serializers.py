from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers
from users.utils.session_merger import merge_anonymous_session

class CustomRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(max_length=255)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['full_name'] = self.validated_data.get('full_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.full_name = self.cleaned_data.get('full_name')
        user.save()
        return user


class CustomLoginSerializer(LoginSerializer):
    anonymous_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        anonymous_id = self.initial_data.get('anonymous_id')
        attrs = super().validate(attrs)
        user = attrs.get('user')

        if user and anonymous_id:
            merge_anonymous_session(user, anonymous_id)

        return attrs
