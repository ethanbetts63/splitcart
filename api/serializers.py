from rest_framework import serializers
from django.utils.text import slugify
from decimal import Decimal
from products.models import Product, Price
from products.models.substitution import ProductSubstitution
from companies.models import Store, Category, PrimaryCategory, Company, PillarPage
from companies.models.postcode import Postcode
from data_management.models import FAQ, BargainStats
from users.models import SelectedStoreList, Cart, CartItem, CartSubstitution

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer')

class BargainStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BargainStats
        fields = ('key', 'data', 'updated_at')

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

    class Meta:
        model = PillarPage
        fields = ('name', 'slug', 'hero_title', 'introduction_paragraph', 'primary_categories')

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
    min_unit_price = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True, required=False)
    slug = serializers.SerializerMethodField()
    bargain_info = serializers.SerializerMethodField()

    # Keep debug fields as requested
    best_discount = serializers.IntegerField(read_only=True, required=False)
    cheaper_store_name = serializers.CharField(read_only=True, required=False)
    cheaper_company_name = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = Product
        fields = ('id', 'name', 'brand_name', 'size', 'image_url', 'prices', 'primary_category', 'min_unit_price', 'slug', 'bargain_info',
                  'best_discount', 'cheaper_store_name', 'cheaper_company_name')

    def _get_filtered_prices(self, obj):
        """
        Internal helper to get the definitive, filtered list of prices for a product.
        Memoizes the result on the object instance to avoid re-computation during
        a single serialization.
        """
        # Check if the prices have already been computed for this object instance
        if hasattr(obj, '_filtered_prices_cache'):
            return obj._filtered_prices_cache

        prices_map = self.context.get('prices_map')
        nearby_store_ids = self.context.get('nearby_store_ids')

        if prices_map is not None:
            prices_queryset = prices_map.get(obj.id, [])
        else:
            # Access the prefetched data; no DB hit occurs here.
            all_prices = obj.prices.all()
            if nearby_store_ids:
                prices_queryset = [p for p in all_prices if p.store_id in nearby_store_ids]
            else:
                prices_queryset = list(all_prices)
        
        # Cache the result on the object instance for this serialization run
        obj._filtered_prices_cache = prices_queryset
        return prices_queryset

    def get_slug(self, obj):
        return f"{slugify(obj.name)}-{obj.id}"

    def get_bargain_info(self, obj):
        """
        Recalculates the bargain for display using the single, consistent,
        filtered price list provided by the internal helper method.
        """
        prices_queryset = self._get_filtered_prices(obj)

        if not prices_queryset or len(prices_queryset) < 2:
            return None

        # Find absolute min price and all companies that have it
        min_price = None
        cheapest_companies = []
        for price_obj in prices_queryset:
            if min_price is None or price_obj.price < min_price:
                min_price = price_obj.price
                cheapest_companies = [price_obj.store.company.name]
            elif price_obj.price == min_price:
                if price_obj.store.company.name not in cheapest_companies:
                    cheapest_companies.append(price_obj.store.company.name)
        
        if min_price is None:
            return None

        # Find the max price from any company NOT in the cheapest list
        max_price_other_company = None
        for price_obj in prices_queryset:
            if price_obj.store.company.name not in cheapest_companies:
                if max_price_other_company is None or price_obj.price > max_price_other_company:
                    max_price_other_company = price_obj.price

        if max_price_other_company and max_price_other_company > min_price:
            discount = int(round(((max_price_other_company - min_price) / max_price_other_company) * 100))
            
            if discount >= 5:
                # Replace "Woolworths" with "Woolies" for display
                display_names = ["Woolies" if name == "Woolworths" else name for name in cheapest_companies]
                display_names.sort()
                company_string = ", ".join(display_names)
                
                return {
                    "discount_percentage": discount,
                    "cheapest_company_name": company_string,
                    "message": f"-{discount}% at {company_string}",
                    "cheapest_company_logo_url": self._get_image_url_for_company(obj, cheapest_companies[0])
                }
                
        return None

    def _get_image_url_for_company(self, product_obj, company_name, company_obj=None):
        """
        A single, reusable method to generate a smaller, optimized image URL for a given product and company.
        """
        company_name_lower = company_name.lower()

        # --- Handle Aldi (special case on product model) ---
        if company_name_lower == 'aldi' and product_obj.aldi_image_url:
            # Replace the width parameter to request a smaller image
            return product_obj.aldi_image_url.replace("/scaleWidth/500/", "/scaleWidth/280/")

        # If company object isn't passed, fetch it
        if not company_obj:
            company_obj = Company.objects.filter(name__iexact=company_name).first()

        if not company_obj:
            return None

        # Get SKU for the company by querying the SKU model
        sku_obj = product_obj.skus.filter(company=company_obj).first()
        if not sku_obj:
            return None
        sku = sku_obj.sku
        sku_str = str(sku)

        # --- Handle Coles (hardcoded URL structure, no resize options) ---
        if company_name_lower == 'coles':
            return f"https://productimages.coles.com.au/productimages/{sku_str[0] if sku_str else '0'}/{sku_str}.jpg"

        # --- Handle companies with a template from the DB ---
        if not company_obj.image_url_template:
            return None
        
        base_url = company_obj.image_url_template.format(sku=sku)

        # --- Handle Woolworths (resize by changing path segment) ---
        if company_name_lower == 'woolworths':
            return base_url.replace("/large/", "/medium/")

        # --- Handle IGA (resize by changing URL parameters) ---
        if company_name_lower == 'iga':
            return base_url.replace("w_500", "w_280").replace("h_500", "h_280")
            
        # For any other company, return the formatted template URL as is
        return base_url

    def get_image_url(self, obj):
        """
        Constructs a single representative image URL for the product tile.
        It prioritizes using the image from the cheapest company if a bargain exists,
        ensuring consistency between the bargain badge and the product image.
        """
        # Attempt to get the accurate bargain info first
        bargain_info = self.get_bargain_info(obj)
        if bargain_info and bargain_info.get('cheapest_company_logo_url'):
            return bargain_info['cheapest_company_logo_url']

        # Fallback to the old method if no bargain is found
        prices_queryset = self._get_filtered_prices(obj)

        for price in prices_queryset:
            if price.store and price.store.company:
                company = price.store.company
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
        """
        Formats the filtered list of prices for frontend display.
        """
        prices_queryset = self._get_filtered_prices(obj)
        
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

            # Find the original price object to get the per_unit_price_string
            # This is not perfectly efficient but necessary for now
            original_price_obj = next((p for p in prices_queryset if p.store.company.name == company_name), None)
            per_unit_price_string = original_price_obj.per_unit_price_string if original_price_obj and original_price_obj.per_unit_price_string else None


            formatted_prices.append({
                'company': company_name,
                'price_display': price_range,
                'is_lowest': is_lowest,
                'image_url': image_url,
                'per_unit_price_string': per_unit_price_string
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
