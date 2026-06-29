from rest_framework import serializers
from django.utils.text import slugify
from products.models import Product
from companies.serializers.primary_category_serializer import PrimaryCategorySerializer

class ProductSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    primary_category = PrimaryCategorySerializer(read_only=True)
    min_unit_price = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True, required=False)
    slug = serializers.SerializerMethodField()
    bargain_info = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'brand_name', 'size', 'image_url', 'prices',
            'primary_category', 'min_unit_price', 'slug', 'bargain_info',
        )

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
            "cheapest_company_name": cheapest_company,
            "message": f"-{discount}% at {display_name}",
        }
        
        obj._bargain_info_cache = result
        return result

    def _get_image_url_for_company(self, product_obj, company_name, company_obj=None):
        """
        A single, reusable method to generate a smaller, optimized image URL for a given product and company.
        """
        company_name_lower = company_name.lower()

        # --- Handle Aldi (special case on product model) ---
        if company_name_lower == 'aldi' and product_obj.aldi_image_url:
            # Replace the width parameter to request a smaller image
            return product_obj.aldi_image_url.replace("/scaleWidth/500/", "/scaleWidth/280/")

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

        # For any other company, return the formatted template URL as is
        return base_url

    def get_image_url(self, obj):
        """
        Constructs a single representative image URL for the product tile.
        It prioritizes using the image from the cheapest company if a bargain exists,
        ensuring consistency between the bargain badge and the product image.
        """
        bargain_info = self.get_bargain_info(obj)
        prices = list(obj.prices.all())

        if bargain_info:
            cheapest_company = bargain_info.get('cheapest_company_name')
            for price in prices:
                if price.company.name == cheapest_company:
                    image_url = self._get_image_url_for_company(obj, price.company.name, company_obj=price.company)
                    if image_url:
                        return image_url

        for price in prices:
            company = price.company
            image_url = self._get_image_url_for_company(obj, company.name, company_obj=company)
            if image_url:
                return image_url
            
        return None

    def get_brand_name(self, obj):
        if obj.brand_name_company_pairs and len(obj.brand_name_company_pairs) > 0:
            # Assuming the structure is [[brand_name, company_name], ...]
            # Return the first element of the first pair
            return obj.brand_name_company_pairs[0][0]
        return None

    def get_prices(self, obj):
        """
        Formats one current price per company for frontend display.
        """
        prices = list(obj.prices.all())
        if not prices:
            return []

        overall_min_price = min(price.price for price in prices)
        formatted_prices = [
            {
                'company': price.company.name,
                'price_display': f"{price.price:.2f}",
                'is_lowest': price.price == overall_min_price,
                'image_url': self._get_image_url_for_company(obj, price.company.name, company_obj=price.company),
                'per_unit_price_string': price.per_unit_price_string or None,
            }
            for price in prices
        ]
        
        # Sort by lowest price first, then company name
        formatted_prices.sort(key=lambda x: (float(x['price_display']), x['company']))

        return formatted_prices
