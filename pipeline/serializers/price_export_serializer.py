from rest_framework import serializers
from products.models import Price

class PriceExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ('product_id', 'company_id', 'price', 'id')
