from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from data_management.models import FAQ
from ..serializers import FaqSerializer

class FaqListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FaqSerializer
    queryset = FAQ.objects.all()

    def list(self, request, *args, **kwargs):
        page = request.query_params.get('page', None)
        queryset = self.get_queryset()

        if page:
            filtered_queryset = [faq for faq in queryset if page in faq.pages]
        else:
            filtered_queryset = []

        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
