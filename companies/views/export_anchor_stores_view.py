from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from companies.models import StoreGroup
from api.permissions import IsInternalAPIRequest

class ExportAnchorStoresView(ListAPIView):
    """
    A view to export all anchor store IDs.
    """
    permission_classes = [IsInternalAPIRequest]

    def get(self, request, *args, **kwargs):
        anchor_ids = StoreGroup.objects.filter(anchor__isnull=False, anchor__prices__isnull=False).values_list('anchor_id', flat=True).distinct()
        return Response(list(anchor_ids))
