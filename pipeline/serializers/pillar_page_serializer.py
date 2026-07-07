from rest_framework import serializers
from companies.models import PillarPage
from companies.serializers.primary_category_serializer import PrimaryCategorySerializer

class PillarPageSerializer(serializers.ModelSerializer):
    primary_categories = PrimaryCategorySerializer(many=True, read_only=True)

    class Meta:
        model = PillarPage
        fields = ('name', 'slug', 'hero_title', 'introduction_paragraph', 'primary_categories')
