from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from data_management.models import FAQ
from data_management.serializers.faq_serializer import FaqSerializer
from django.views.decorators.cache import cache_page 
from django.utils.decorators import method_decorator 

@method_decorator(cache_page(60 * 60 * 24), name='dispatch') # Apply 24-hour cache
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
