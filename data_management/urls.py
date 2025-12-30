from django.urls import path
from .views.product_file_upload_view import ProductFileUploadView
from .views.gs1_file_upload_view import Gs1FileUploadView
from .views.store_file_upload_view import StoreFileUploadView
from .views.category_links_file_upload_view import CategoryLinksFileUploadView
from .views.scheduler_view import SchedulerView
from .views.faq_list_view import FaqListView
from .views.pillar_page_view import PillarPageView
from .views.product_translation_file_view import ProductTranslationFileView
from .views.brand_translation_file_view import BrandTranslationFileView
from .views.import_semantic_data_view import ImportSemanticDataView
from .views.gs1_views import GS1UnconfirmedBrandsView, BrandSampleBarcodeView

urlpatterns = [
    path('scheduler/next-candidate/', SchedulerView.as_view(), name='scheduler-next-candidate'),
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='gs1-file-upload'),
    path('upload/stores/', StoreFileUploadView.as_view(), name='store-file-upload'),
    path('upload/category-links/', CategoryLinksFileUploadView.as_view(), name='category-links-file-upload'),
    path('gs1/unconfirmed-brands/', GS1UnconfirmedBrandsView.as_view(), name='gs1-unconfirmed-brands'),
    path('brands/<int:brand_id>/sample-barcode/', BrandSampleBarcodeView.as_view(), name='brand-sample-barcode'),
    path('pillar-pages/<slug:slug>/', PillarPageView.as_view(), name='pillar-page-detail'),
    path('faqs/', FaqListView.as_view(), name='faq-list'),
    path('files/product_translations/', ProductTranslationFileView.as_view(), name='product-translation-file'),
    path('files/brand_translations/', BrandTranslationFileView.as_view(), name='brand-translation-file'),
    path('import/semantic_data/', ImportSemanticDataView.as_view(), name='import-semantic-data'),
]