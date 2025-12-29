from rest_framework import serializers
from users.models import CartItem
from products.models import Product
from cart_substitution_serializer import CartSubstitutionSerializer
from products.serializers.product_serializer import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    substitutions = CartSubstitutionSerializer(many=True, read_only=True, source='chosen_substitutions')

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'substitutions', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Replace product ID with full product data
        representation['product'] = ProductSerializer(instance.product, context=self.context).data
        return representation
