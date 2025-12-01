from rest_framework import serializers
from users.models import CartItem, CartSubstitution
from .product_serializer import ProductSerializer

class CartSubstitutionSerializer(serializers.ModelSerializer):
    original_cart_item = serializers.PrimaryKeyRelatedField(queryset=CartItem.objects.all())
    substituted_product = ProductSerializer(read_only=True)

    class Meta:
        model = CartSubstitution
        fields = ('id', 'original_cart_item', 'substituted_product', 'quantity', 'is_approved', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
