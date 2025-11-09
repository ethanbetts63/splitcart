from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product, ProductBrand
from api.permissions import IsInternalAPICall

class GS1UnconfirmedBrandsView(APIView):
    permission_classes = [IsInternalAPICall]

    def get(self, request, *args, **kwargs):
        unconfirmed_brands = []
        all_brands = ProductBrand.objects.all()

        for brand in all_brands:
            if brand.confirmed_official_prefix:
                continue
            
            count = Product.objects.filter(brand=brand).count()
            if count > 0:
                unconfirmed_brands.append({'brand': brand, 'count': count})
        
        sorted_brands = sorted(unconfirmed_brands, key=lambda x: x['count'], reverse=True)
        
        # Return only the top 30 brands, as per the scraper's current logic
        top_30_brands_data = []
        for brand_info in sorted_brands[:30]:
            top_30_brands_data.append({
                'brand_id': brand_info['brand'].id,
                'brand_name': brand_info['brand'].name,
            })
        
        return Response(top_30_brands_data, status=status.HTTP_200_OK)

class BrandSampleBarcodeView(APIView):
    permission_classes = [IsInternalAPICall]

    def get(self, request, brand_id, *args, **kwargs):
        try:
            brand = ProductBrand.objects.get(id=brand_id)
        except ProductBrand.DoesNotExist:
            return Response({"detail": "Brand not found."}, status=status.HTTP_404_NOT_FOUND)
        
        product_with_barcode = Product.objects.filter(
            brand=brand
        ).exclude(barcode__isnull=True).exclude(barcode__exact='').first()

        if product_with_barcode and product_with_barcode.barcode:
            return Response({"barcode": product_with_barcode.barcode}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "No product with barcode found for this brand."}, status=status.HTTP_404_NOT_FOUND)
