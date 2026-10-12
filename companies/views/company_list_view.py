from rest_framework.generics import ListAPIView
from companies.models import Company
from companies.serializers.company_serializer import CompanySerializer
from config.permissions import IsInternalAPIRequest

class CompanyListView(ListAPIView):
    """
    Provides a list of all companies.
    """
    queryset = Company.objects.all().order_by('pk')
    serializer_class = CompanySerializer
    permission_classes = [IsInternalAPIRequest]
    # The pipeline's own scope, like every other internal export. Unscoped, it
    # answered with no limit at all until ftp_security.E006 found it.
    throttle_scope = 'internal'
