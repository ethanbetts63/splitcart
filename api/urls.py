from django.urls import path
from .views.file_upload_view import FileUploadView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]
