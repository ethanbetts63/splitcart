from rest_framework import serializers
from products.models import Price

class PriceExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ('product_id', 'store_id', 'price', 'id')
