from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from companies.models import Postcode
from companies.serializers import PostcodeSerializer
import sys
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class PostcodeSearchView(ListAPIView):
    serializer_class = PostcodeSerializer

    def get_queryset(self):
        postcode = self.request.query_params.get('postcode', '').strip()
        print(f"Searching for postcode: '{postcode}'", file=sys.stderr)
        if postcode:
            queryset = Postcode.objects.filter(postcode__exact=postcode)
            print(f"Queryset: {queryset.query}", file=sys.stderr)
            print(f"Queryset count: {queryset.count()}", file=sys.stderr)
            return queryset
        return Postcode.objects.none()

    def list(self, request, *args, **kwargs):
        print("PostcodeSearchView.list called", file=sys.stderr)
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)
        print("Postcode not found, returning 404", file=sys.stderr)
        return Response(status=404)