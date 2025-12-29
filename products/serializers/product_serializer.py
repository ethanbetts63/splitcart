from rest_framework import serializers
from django.utils.text import slugify
from products.models import Product
from companies.models import Company
from companies.serializers.primary_category_serializer import PrimaryCategorySerializer

class ProductSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    primary_category = PrimaryCategorySerializer(read_only=True)
    min_unit_price = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True, required=False)
    slug = serializers.SerializerMethodField()
    bargain_info = serializers.SerializerMethodField()

    # Keep debug fields, but convert to SerializerMethodFields to use context data
    best_discount = serializers.SerializerMethodField()
    cheaper_store_name = serializers.SerializerMethodField()
    cheaper_company_name = serializers.SerializerMethodField()

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
        Reads pre-calculated bargain info from the serializer context, provided by the view.
        This avoids re-calculating logic and ensures the data is consistent with the view's sorting.
        """
        # Memoize the result to avoid re-calculating for other method fields
        if hasattr(obj, '_bargain_info_cache'):
            return obj._bargain_info_cache

        bargain_info_map = self.context.get('bargain_info_map')
        if not bargain_info_map:
            obj._bargain_info_cache = None
            return None

        bargain_data = bargain_info_map.get(obj.id)
        if not bargain_data:
            obj._bargain_info_cache = None
            return None
        
        discount = bargain_data.get('discount')
        cheapest_company = bargain_data.get('cheaper_company_name', 'Unknown')
        
        # Replace "Woolworths" with "Woolies" for display
        display_name = "Woolies" if cheapest_company == "Woolworths" else cheapest_company
        
        result = {
            "discount_percentage": discount,
            "cheapest_company_name": cheapest_company, # Keep original name for grouping
            "message": f"-{discount}% at {display_name}",
            "cheapest_company_logo_url": bargain_data.get('cheaper_company_logo_url')
        }
        
        obj._bargain_info_cache = result
        return result

    def get_best_discount(self, obj):
        bargain_info = self.get_bargain_info(obj)
        return bargain_info.get('discount_percentage') if bargain_info else None

    def get_cheaper_store_name(self, obj):
        # The new view logic provides company name, not store name, for the top-level bargain.
        # This can be adjusted if store-level detail is needed again.
        bargain_info_map = self.context.get('bargain_info_map', {})
        bargain_data = bargain_info_map.get(obj.id)
        return bargain_data.get('cheaper_store_name') if bargain_data else None

    def get_cheaper_company_name(self, obj):
        bargain_info = self.get_bargain_info(obj)
        return bargain_info.get('cheapest_company_name') if bargain_info else None

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
