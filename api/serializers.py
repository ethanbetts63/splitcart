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
        nearby_store_ids = self.context.get('nearby_store_ids')
        
        # Start with all prices for the product, ordered by price
        prices_queryset = Price.objects.filter(price_record__product=obj).order_by('price_record__price')

        # If nearby_store_ids are provided in the context, filter by them
        if nearby_store_ids is not None:
            prices_queryset = prices_queryset.filter(store__id__in=nearby_store_ids)
            
        return PriceSerializer(prices_queryset, many=True).data
