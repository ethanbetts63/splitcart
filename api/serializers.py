from rest_framework import serializers
from products.models import Product, Price

class PriceSerializer(serializers.ModelSerializer):
    store = serializers.StringRelatedField()
    price = serializers.DecimalField(source='price_record.price', max_digits=10, decimal_places=2)

    class Meta:
        model = Price
        fields = ('store', 'price')

class ProductSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'image_url', 'prices')

    def get_prices(self, obj):
        # Get active prices for the product, ordered by price
        active_prices = Price.objects.filter(price_record__product=obj).order_by('price_record__price')
        return PriceSerializer(active_prices, many=True).data
