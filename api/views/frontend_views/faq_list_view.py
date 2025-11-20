from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from data_management.models import FAQ
from ...serializers import FaqSerializer
from django.views.decorators.cache import cache_page # New import
from django.utils.decorators import method_decorator # New import

@method_decorator(cache_page(3600), name='dispatch') # Apply cache_page decorator
class FaqListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FaqSerializer
    queryset = FAQ.objects.all()

    def list(self, request, *args, **kwargs):
        page = request.query_params.get('page', None)
        queryset = self.get_queryset()

        if page:
            queryset = queryset.filter(pages__contains=page)
        else:
            # If no page is specified, return an empty queryset as per original logic
            queryset = queryset.none()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
