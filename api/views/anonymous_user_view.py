import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import SelectedStoreList

class AnonymousUserCreateView(APIView):
    def post(self, request, *args, **kwargs):
        anonymous_id = uuid.uuid4()

        # Create a default store list for the anonymous user
        # This assumes a default set of stores can be determined
        # For now, we'll create an empty store list
        default_store_list = SelectedStoreList.objects.create(
            anonymous_id=anonymous_id,
            name="Default List"
        )
        # You might want to add some default stores here, e.g.:
        # default_stores = Store.objects.filter(company__name__in=['Coles', 'Woolworths'])
        # default_store_list.stores.set(default_stores)

        return Response({'anonymous_id': anonymous_id}, status=status.HTTP_201_CREATED)
