from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers
from .models.selected_store_list import SelectedStoreList


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

        # Perform default validation first to get the user object
        attrs = super().validate(attrs)
        user = attrs.get('user')

        if user and anonymous_id:
            try:
                anon_list = SelectedStoreList.objects.get(anonymous_id=anonymous_id)

                # Case 1: Anonymous list has stores
                if anon_list.stores.exists():
                    # Transfer ownership
                    anon_list.user = user
                    anon_list.anonymous_id = None
                    anon_list.save()
                else:
                    # Case 2: Anonymous list is empty
                    # Check if the user has other lists with items
                    user_has_lists_with_items = user.store_lists.filter(stores__isnull=False).exists()

                    if user_has_lists_with_items:
                        # If user has other populated lists, delete the empty anonymous one
                        anon_list.delete()
                    else:
                        # Otherwise, transfer the empty list
                        anon_list.user = user
                        anon_list.anonymous_id = None
                        anon_list.save()

            except SelectedStoreList.DoesNotExist:
                # No anonymous list found, do nothing
                pass

        return attrs
