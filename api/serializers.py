from rest_framework import serializers
from products.models import Product, Price
from products.models.substitution import ProductSubstitution
from companies.models import Store, Category, PrimaryCategory, Company, PillarPage
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
        fields = ('name', 'slug', 'price_comparison_data')

class PillarPageSerializer(serializers.ModelSerializer):
    primary_categories = PrimaryCategorySerializer(many=True, read_only=True)
    faqs = FaqSerializer(many=True, read_only=True)

    class Meta:
        model = PillarPage
        fields = ('name', 'slug', 'hero_title', 'introduction_paragraph', 'image_path', 'primary_categories', 'faqs')

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

    def _get_image_url_for_company(self, product_obj, company_name, company_obj=None):
        """
        A single, reusable method to generate an image URL for a given product and company.
        """
        # Handle Aldi first, as it's a special case on the product itself
        if company_name.lower() == 'aldi' and product_obj.aldi_image_url:
            return product_obj.aldi_image_url

        # If company object isn't passed, fetch it
        if not company_obj:
            company_obj = Company.objects.filter(name__iexact=company_name).first()

        if not company_obj or not company_obj.image_url_template:
            return None

        # Get SKU for the company by querying the SKU model
        sku_obj = product_obj.skus.filter(company=company_obj).first()

        if not sku_obj:
            return None
        
        sku = sku_obj.sku
        sku_str = str(sku)

        # Handle Coles' special URL structure
        if company_name.lower() == 'coles':
            first_digit = sku_str[0] if sku_str else '0'
            return f"https://productimages.coles.com.au/productimages/{first_digit}/{sku_str}.jpg"
        
        # Handle all other companies with a template
        return company_obj.image_url_template.format(sku=sku)

    def get_image_url(self, obj):
        """
        Constructs a single representative image URL for the product.
        It iterates through the available prices until it finds a company
        for which it can generate a valid image URL.
        """
        # Use the prices from the context if available, otherwise fetch them.
        prices_map = self.context.get('prices_map')
        if prices_map is not None:
            prices_queryset = prices_map.get(obj.id, [])
        else:
            prices_queryset = obj.prices.select_related('store__company').all()

        for price in prices_queryset:
            if price.store and price.store.company:
                company = price.store.company
                # Try to generate a URL for this company
                image_url = self._get_image_url_for_company(obj, company.name, company_obj=company)
                if image_url:
                    return image_url # Return the first valid URL we find
            
        return None # Return None if no valid URL could be generated

    def get_brand_name(self, obj):
        if obj.brand_name_company_pairs and len(obj.brand_name_company_pairs) > 0:
            # Assuming the structure is [[brand_name, company_name], ...]
            # Return the first element of the first pair
            return obj.brand_name_company_pairs[0][0]
        return None

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

            # Call the reusable helper method to get the image URL
            image_url = self._get_image_url_for_company(obj, company_name)

            formatted_prices.append({
                'company': company_name,
                'price_display': price_range,
                'is_lowest': is_lowest,
                'image_url': image_url,
                'per_unit_price_string': price_obj.per_unit_price_string if price_obj.per_unit_price_string else None
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
