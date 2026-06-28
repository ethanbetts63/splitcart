from rest_framework import serializers
from users.models import Cart
from .cart_item_serializer import CartItemSerializer

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'items', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
