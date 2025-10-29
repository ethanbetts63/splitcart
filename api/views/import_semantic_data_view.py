from rest_framework import views, response, status
from rest_framework.permissions import IsAdminUser
from products.models import Product, ProductSubstitution
from companies.models import Category, CategoryLink

class ImportSemanticDataView(views.APIView):
    """
    API endpoint to import semantic analysis results.
    Expects a JSON payload with 'category_links' and 'substitutions'.
    This endpoint should be protected and only accessible by admins.
    """
    permission_classes = [IsAdminUser] # Important for security

    def post(self, request, *args, **kwargs):
        data = request.data
        category_links_data = data.get('category_links', [])
        substitutions_data = data.get('substitutions', [])

        new_links = []
        for link_data in category_links_data:
            new_links.append(CategoryLink(
                category_a_id=link_data['category_a'],
                category_b_id=link_data['category_b'],
                link_type=link_data['link_type']
            ))
        
        new_substitutions = []
        for sub_data in substitutions_data:
            new_substitutions.append(ProductSubstitution(
                product_a_id=sub_data['product_a'],
                product_b_id=sub_data['product_b'],
                level=sub_data['level'],
                score=sub_data['score'],
                source=sub_data['source']
            ))

        try:
            links_created = CategoryLink.objects.bulk_create(new_links, ignore_conflicts=True)
            subs_created = ProductSubstitution.objects.bulk_create(new_substitutions, ignore_conflicts=True)
            return response.Response(
                {
                    'status': 'success',
                    'category_links_created': len(links_created),
                    'substitutions_created': len(subs_created)
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return response.Response(
                {'error': f'An error occurred during bulk creation: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
