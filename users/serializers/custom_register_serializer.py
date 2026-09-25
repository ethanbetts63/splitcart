from dj_rest_auth.registration.serializers import RegisterSerializer
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

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['full_name'] = self.validated_data.get('full_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.full_name = self.cleaned_data.get('full_name')
        user.save()
        return user
