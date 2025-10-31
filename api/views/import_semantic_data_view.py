from rest_framework import views, response, status
from api.permissions import IsInternalAPIRequest
from products.models import ProductSubstitution
from companies.models import CategoryLink

class ImportSemanticDataView(views.APIView):
    """
    API endpoint to import semantic analysis results from local commands.
    Expects a JSON payload with 'category_links' and/or 'substitutions'.
    This endpoint should be protected and only accessible by admins or via API Key.
    """
    permission_classes = [IsInternalAPIRequest]

    def post(self, request, *args, **kwargs):
        data = request.data
        category_links_data = data.get('category_links', [])
        substitutions_data = data.get('substitutions', [])
        
        links_created_count = 0
        subs_created_count = 0

        try:
            if category_links_data:
                new_links = []
                for link_data in category_links_data:
                    new_links.append(CategoryLink(
                        category_a_id=link_data['category_a'],
                        category_b_id=link_data['category_b'],
                        link_type=link_data['link_type']
                    ))
                # ignore_conflicts=True prevents errors if a link already exists
                created_links = CategoryLink.objects.bulk_create(new_links, ignore_conflicts=True)
                links_created_count = len(created_links)

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
                    'category_links_created': links_created_count,
                    'substitutions_created': subs_created_count
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return response.Response(
                {'error': f'An error occurred during bulk creation: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )