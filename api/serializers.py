from rest_framework import serializers
from products.models import Product, Price
from products.models.substitution import ProductSubstitution
from companies.models import Store, Category, PrimaryCategory, Company
from companies.models.postcode import Postcode
from data_management.models import FAQ
from users.models import SelectedStoreList, Cart, CartItem, CartSubstitution

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')

class CategoryWithProductsExportSerializer(serializers.ModelSerializer):
    company = serializers.StringRelatedField(source='company')
    product_ids = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'company', 'parents', 'product_ids')

    def get_product_ids(self, obj):
        return list(obj.products.values_list('id', flat=True))

class PrimaryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaryCategory
        fields = ('name', 'slug')

class StoreSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name')

    class Meta:
        model = Store
        fields = ('id', 'store_name', 'latitude', 'longitude', 'company_name')

class StoreExportSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source='company.name')
    division = serializers.CharField(source='division.name', allow_null=True)

    class Meta:
        model = Store
        fields = ('id', 'company', 'division', 'latitude', 'longitude')


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
    price = serializers.DecimalField(source='price', max_digits=10, decimal_places=2)

    class Meta:
        model = Price
        fields = ('store', 'price')

class PriceExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ('product_id', 'store_id', 'price', 'id')

class ProductSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    primary_category = PrimaryCategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'brand_name', 'size', 'image_url', 'prices', 'primary_category')

    def get_image_url(self, obj):
        """
        Constructs the image URL based on the company's template or aldi_image_url.
        """
        if obj.aldi_image_url:
            return obj.aldi_image_url

        # Assuming a product will have at least one price associated with a store/company
        # to determine its company for the template.
        # This might need optimization if products can exist without prices.
        first_price = obj.price_set.select_related('store__company').first()
        if first_price and first_price.store and first_price.store.company:
            company = first_price.store.company
            if company.image_url_template and obj.sku:
                # Assuming product.sku is the correct identifier for the template
                return company.image_url_template.format(sku=obj.sku)
        return None

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
            prices_queryset = Price.objects.filter(product=obj)
            # Prefetch store and company to avoid N+1 queries in the loop
            prices_queryset = prices_queryset.select_related('store__company')

        company_prices = {}
        overall_min_price = None

        for price_obj in prices_queryset:
            company_name = price_obj.store.company.name
            current_price = price_obj.price

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
        for company_name, data in company_prices.items():
            price_range = f"{data['min_price']:.2f}"
            if data['min_price'] != data['max_price']:
                price_range = f"{data['min_price']:.2f} - {data['max_price']:.2f}"
            
            is_lowest = (data['min_price'] == overall_min_price) if overall_min_price is not None else False

            # Dynamically construct image_url
            image_url = None
            if obj.aldi_image_url and company_name.lower() == 'aldi':
                image_url = obj.aldi_image_url
            else:
                # Find the company object to get its template
                company_obj = Company.objects.filter(name__iexact=company_name).first()
                if company_obj and company_obj.image_url_template and obj.sku:
                    image_url = company_obj.image_url_template.format(sku=obj.sku)

            formatted_prices.append({
                'company': company_name,
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
