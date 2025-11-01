from rest_framework.generics import ListAPIView
from companies.models import Category
from api.serializers import CategoryWithProductsExportSerializer
from api.permissions import IsInternalAPIRequest
from rest_framework.throttling import ScopedRateThrottle

class ExportCategoriesWithProductsView(ListAPIView):
    """
    A view to export all category data with associated product IDs.
    """
    queryset = Category.objects.all().select_related('company').prefetch_related('products')
    serializer_class = CategoryWithProductsExportSerializer
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    def get(self, request, *args, **kwargs):
        print("ExportCategoriesWithProductsView is being called")
        return super().get(request, *args, **kwargs)
