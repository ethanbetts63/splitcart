from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from companies.models import PillarPage
from data_management.models import FAQ
from api.serializers import PillarPageSerializer
from django.http import Http404

class PillarPageView(RetrieveAPIView):
    """
    API view to retrieve a Pillar Page by its slug.
    """
    queryset = PillarPage.objects.prefetch_related('primary_categories').all()
    serializer_class = PillarPageSerializer
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response({"detail": "Pillar page not found."}, status=404)

        # --- START DEBUGGING ---
        print("--- DEBUGGING PillarPageView ---")
        print(f"Pillar Page Instance: {instance.name} (ID: {instance.id})")
        related_categories_manager = instance.primary_categories
        print(f"Related Manager: {related_categories_manager}")
        try:
            related_categories_queryset = related_categories_manager.all()
            print(f"Related Categories QuerySet: {related_categories_queryset}")
            print(f"Count of Related Categories: {related_categories_queryset.count()}")
            print(f"List of Related Categories: {list(related_categories_queryset)}")
        except Exception as e:
            print(f"Error accessing related categories: {e}")
        print("--- END DEBUGGING ---")
        # --- END DEBUGGING ---

        # The serializer expects related 'faqs' to be on the instance.
        # We need to fetch them separately and attach them.
        # The 'pages' field in FAQ is a JSONField (list of strings).
        instance.faqs = FAQ.objects.filter(pages__contains=instance.slug)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
