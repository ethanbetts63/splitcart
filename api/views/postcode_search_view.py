from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from companies.models import Postcode
from ..serializers import PostcodeSerializer

class PostcodeSearchView(ListAPIView):
    serializer_class = PostcodeSerializer

    def get_queryset(self):
        postcode = self.request.query_params.get('postcode', None)
        if postcode:
            return Postcode.objects.filter(postcode=postcode)
        return Postcode.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)
        return Response(status=404)