from rest_framework import serializers
from products.models import Product, Price
from products.models.substitution import ProductSubstitution

class ProductSubstitutionSerializer(serializers.ModelSerializer):
    level_description = serializers.SerializerMethodField()

    class Meta:
        model = ProductSubstitution
        fields = ('level', 'level_description', 'score')

    def get_level_description(self, obj):
        return obj.get_level_display()

    def to_representation(self, instance):
        representation = {
            'level': instance.level,
            'level_description': self.get_level_description(instance),
            'score': instance.score,
        }

        original_product_id = self.context.get('original_product_id')
        if instance.product_a.id == original_product_id:
            substitute_product = instance.product_b
        else:
            substitute_product = instance.product_a

        product_data = ProductSerializer(substitute_product, context=self.context).data
        representation.update(product_data)

        return representation

class PriceSerializer(serializers.ModelSerializer):
    store = serializers.StringRelatedField()
    price = serializers.DecimalField(source='price_record.price', max_digits=10, decimal_places=2)

    class Meta:
        model = Price
        fields = ('store', 'price')

class ProductSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'brand_name', 'size', 'image_url', 'prices')

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None

    def get_prices(self, obj):
        nearby_store_ids = self.context.get('nearby_store_ids')
        
        # Start with all prices for the product
        prices_queryset = Price.objects.filter(price_record__product=obj)

        # If nearby_store_ids are provided in the context, filter by them
        if nearby_store_ids is not None:
            prices_queryset = prices_queryset.filter(store__id__in=nearby_store_ids)
        
        # Group prices by company and calculate min/max
        company_prices = {}
        overall_min_price = None

        # Prefetch store and company to avoid N+1 queries in the loop
        prices_queryset = prices_queryset.select_related('store__company', 'price_record')

        for price_obj in prices_queryset:
            company_name = price_obj.store.company.name
            current_price = price_obj.price_record.price

            if company_name not in company_prices:
                company_prices[company_name] = {
                    'min_price': current_price,
                    'max_price': current_price,
                    'prices': [] # Store all prices for potential future use/sorting
                }
            else:
                company_prices[company_name]['min_price'] = min(company_prices[company_name]['min_price'], current_price)
                company_prices[company_name]['max_price'] = max(company_prices[company_name]['max_price'], current_price)
            
            company_prices[company_name]['prices'].append(current_price)

            if overall_min_price is None or current_price < overall_min_price:
                overall_min_price = current_price
        
        # Format the output for the frontend
        formatted_prices = []
        for company, data in company_prices.items():
            price_range = f"{data['min_price']:.2f}"
            if data['min_price'] != data['max_price']:
                price_range = f"{data['min_price']:.2f} - {data['max_price']:.2f}"
            
            is_lowest = (data['min_price'] == overall_min_price) if overall_min_price is not None else False

            formatted_prices.append({
                'company': company,
                'price_display': price_range,
                'is_lowest': is_lowest
            })
        
        # Sort by lowest price first, then company name
        formatted_prices.sort(key=lambda x: (float(x['price_display'].split(' ')[0]), x['company']))

        return formatted_prices
