from rest_framework import serializers
from companies.models import PrimaryCategory

class PrimaryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaryCategory
        fields = ('name', 'slug', 'price_comparison_data')
