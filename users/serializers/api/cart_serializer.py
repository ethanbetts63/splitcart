from rest_framework import serializers
from users.models import Cart, SelectedStoreList
from .selected_store_list_serializer import SelectedStoreListSerializer
from .cart_item_serializer import CartItemSerializer

class CartSerializer(serializers.ModelSerializer):
    selected_store_list = SelectedStoreListSerializer(read_only=True)
    selected_store_list_id = serializers.PrimaryKeyRelatedField(
        queryset=SelectedStoreList.objects.all(), source='selected_store_list', write_only=True, required=False
    )
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'selected_store_list', 'selected_store_list_id', 'items', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
