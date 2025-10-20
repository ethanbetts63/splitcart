from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..utils import generate_shopping_list_pdf

class DownloadShoppingListView(APIView):
    """
    An API view to generate and download a shopping list as a PDF.
    Accepts a POST request with a 'shopping_plan' in the body.
    """
    def post(self, request, *args, **kwargs):
        shopping_plan = request.data.get('shopping_plan')
        if not shopping_plan:
            return Response(
                {"error": "Shopping plan data is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_data = generate_shopping_list_pdf(shopping_plan)

        if pdf_data:
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="shopping-list.pdf"'
            return response
        
        return Response(
            {"error": "Failed to generate PDF."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class EmailShoppingListView(APIView):
    """
    An API view to generate and email a shopping list as a PDF attachment.
    Accepts a POST request with a 'shopping_plan' in the body.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        shopping_plan = request.data.get('shopping_plan')
        if not shopping_plan:
            return Response(
                {"error": "Shopping plan data is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_data = generate_shopping_list_pdf(shopping_plan)

        if not pdf_data:
            return Response(
                {"error": "Failed to generate PDF for emailing."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            subject = "Your SplitCart Shopping List"
            body = "Here is your shopping list, as requested. See the attached PDF."
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = request.user.email

            email = EmailMultiAlternatives(subject, body, from_email, [to_email])
            email.attach('shopping-list.pdf', pdf_data, 'application/pdf')
            email.send()

            return Response(
                {"success": "Email sent successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # In a real app, you'd want to log this exception
            print(f"Email sending error: {e}")
            return Response(
                {"error": "An error occurred while sending the email."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
