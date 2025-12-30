from rest_framework import serializers
from companies.models import Store

class StoreExportSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='company.name')
    division = serializers.CharField(source='division.name', allow_null=True)

    class Meta:
        model = Store
        fields = ('id', 'company', 'division', 'latitude', 'longitude')
