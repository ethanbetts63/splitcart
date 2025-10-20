from rest_framework.views import exception_handler
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now, add the handling for IntegrityError
    if isinstance(exc, IntegrityError) and 'users_user.email' in str(exc):
        return Response({'email': ['This email address is already in use.']}, status=status.HTTP_400_BAD_REQUEST)

    return response
