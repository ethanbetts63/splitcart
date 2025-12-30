from rest_framework import generics
from companies.models import PrimaryCategory
from companies.serializers.primary_category_serializer import PrimaryCategorySerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class PrimaryCategoryListView(generics.ListAPIView):
    serializer_class = PrimaryCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return PrimaryCategory.objects.all().order_by('name')
