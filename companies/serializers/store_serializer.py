from rest_framework import serializers
from companies.models import Store

class StoreSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name')

    class Meta:
        model = Store
        fields = ('id', 'store_name', 'latitude', 'longitude', 'company_name')
