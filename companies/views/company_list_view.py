from rest_framework.generics import ListAPIView
from companies.models import Company
from companies.serializers import CompanySerializer
from api.permissions import IsInternalAPIRequest

class CompanyListView(ListAPIView):
    """
    Provides a list of all companies.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsInternalAPIRequest]
