from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from data_management.models import FAQ
from ..serializers import FaqSerializer

class FaqListView(ListAPIView):
    serializer_class = FaqSerializer

    def get_queryset(self):
        page = self.request.query_params.get('page', None)
        if page:
            return FAQ.objects.filter(page=page)
        return FAQ.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
