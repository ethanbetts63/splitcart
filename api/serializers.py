from rest_framework import serializers
from products.models import Product, Price
from products.models.substitution import ProductSubstitution
from companies.models import Store, Category, PopularCategory
from companies.models.postcode import Postcode
from data_management.models import FAQ
from users.models import SelectedStoreList, Cart, CartItem, CartSubstitution

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')

class PopularCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopularCategory
        fields = ('name', 'slug')

class StoreSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name')

    class Meta:
        model = Store
        fields = ('id', 'store_name', 'latitude', 'longitude', 'company_name')


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
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'brand_name', 'size', 'image_url', 'prices')

    def get_image_url(self, obj):
        """
        Deterministically select one image URL from the available pairs.
        """
        if not obj.image_url_pairs:
            return None

        # Get a list of non-empty URLs from the pairs
        # Each pair is [company_name, image_url]
        urls = [pair[1] for pair in obj.image_url_pairs if pair and len(pair) == 2 and pair[1]]
        if not urls:
            return None

        # Deterministic selection using product ID
        return urls[obj.id % len(urls)]

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None

    def get_prices(self, obj):
        prices_map = self.context.get('prices_map')
        nearby_store_ids = self.context.get('nearby_store_ids')

        if prices_map is not None:
            # Use the pre-fetched prices from the context
            prices_queryset = prices_map.get(obj.id, [])
        else:
            # Fallback to the original query if the map is not provided
            prices_queryset = Price.objects.filter(price_record__product=obj)
            # Prefetch store and company to avoid N+1 queries in the loop
            prices_queryset = prices_queryset.select_related('store__company', 'price_record')

        company_prices = {}
        overall_min_price = None

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
        
        image_urls_by_company = dict(obj.image_url_pairs)

        # Format the output for the frontend
        formatted_prices = []
        for company, data in company_prices.items():
            price_range = f"{data['min_price']:.2f}"
            if data['min_price'] != data['max_price']:
                price_range = f"{data['min_price']:.2f} - {data['max_price']:.2f}"
            
            is_lowest = (data['min_price'] == overall_min_price) if overall_min_price is not None else False

            image_url = image_urls_by_company.get(company)

            formatted_prices.append({
                'company': company,
                'price_display': price_range,
                'is_lowest': is_lowest,
                'image_url': image_url
            })
        
        # Sort by lowest price first, then company name
        formatted_prices.sort(key=lambda x: (float(x['price_display'].split(' ')[0]), x['company']))

        return formatted_prices

class PostcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Postcode
        fields = ('postcode', 'latitude', 'longitude', 'state')


class SelectedStoreListSerializer(serializers.ModelSerializer):
    stores = serializers.PrimaryKeyRelatedField(many=True, queryset=Store.objects.all())

    class Meta:
        model = SelectedStoreList
        fields = ('id', 'name', 'stores', 'created_at', 'updated_at', 'last_used_at')
        read_only_fields = ('created_at', 'updated_at', 'last_used_at')


class CartSubstitutionSerializer(serializers.ModelSerializer):
    original_cart_item = serializers.PrimaryKeyRelatedField(queryset=CartItem.objects.all())
    substituted_product = ProductSerializer(read_only=True)

    class Meta:
        model = CartSubstitution
        fields = ('id', 'original_cart_item', 'substituted_product', 'quantity', 'is_approved', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    substitutions = CartSubstitutionSerializer(many=True, read_only=True, source='chosen_substitutions')

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'substitutions', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Replace product ID with full product data
        representation['product'] = ProductSerializer(instance.product, context=self.context).data
        return representation


class CartSerializer(serializers.ModelSerializer):
    selected_store_list = SelectedStoreListSerializer(read_only=True)
    selected_store_list_id = serializers.PrimaryKeyRelatedField(
        queryset=SelectedStoreList.objects.all(), source='selected_store_list', write_only=True, required=False
    )
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'selected_store_list', 'selected_store_list_id', 'items', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
