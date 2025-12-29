from rest_framework import serializers
from products.models import Price

class PriceSerializer(serializers.ModelSerializer):
    store = serializers.StringRelatedField()
    price = serializers.DecimalField(source='price', max_digits=10, decimal_places=2)

    class Meta:
        model = Price
        fields = ('store', 'price')
