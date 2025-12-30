from rest_framework import views, response, status
from rest_framework.throttling import ScopedRateThrottle
from splitcart.permissions import IsInternalAPIRequest
from products.models import ProductSubstitution

class ImportSemanticDataView(views.APIView):
    """
    API endpoint to import semantic analysis results from local commands.
    Expects a JSON payload with 'category_links' and/or 'substitutions'.
    This endpoint should be protected and only accessible by admins or via API Key.
    """
    permission_classes = [IsInternalAPIRequest]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'internal'

    def post(self, request, *args, **kwargs):
        data = request.data
        substitutions_data = data.get('substitutions', [])
        
        subs_created_count = 0

        try:
            if substitutions_data:
                new_substitutions = []
                for sub_data in substitutions_data:
                    new_substitutions.append(ProductSubstitution(
                        product_a_id=sub_data['product_a'],
                        product_b_id=sub_data['product_b'],
                        level=sub_data['level'],
                        score=sub_data['score'],
                        source=sub_data['source']
                    ))
                created_subs = ProductSubstitution.objects.bulk_create(new_substitutions, ignore_conflicts=True)
                subs_created_count = len(created_subs)

            return response.Response(
                {
                    'status': 'success',
                    'substitutions_created': subs_created_count
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return response.Response(
                {'error': f'An error occurred during bulk creation: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )