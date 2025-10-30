from rest_framework import generics
from django.db.models import Count
from companies.models import PopularCategory
from ...serializers import PopularCategorySerializer

class PopularCategoryListView(generics.ListAPIView):
    serializer_class = PopularCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return PopularCategory.objects.annotate(
            num_companies=Count('categories__company', distinct=True)
        ).order_by('-num_companies', 'name')
