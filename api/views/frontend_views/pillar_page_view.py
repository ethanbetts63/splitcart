from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from companies.models import PillarPage
from data_management.models import FAQ
from api.serializers import PillarPageSerializer
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

#@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class PillarPageView(RetrieveAPIView):
    """
    API view to retrieve a Pillar Page by its slug.
    """
    queryset = PillarPage.objects.prefetch_related('primary_categories').all()
    serializer_class = PillarPageSerializer
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"detail": "Pillar page not found."}, status=404)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
