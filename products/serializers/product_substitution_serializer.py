from rest_framework import serializers
from products.models.substitution import ProductSubstitution
from .product_serializer import ProductSerializer

class ProductSubstitutionSerializer(serializers.ModelSerializer):
    level_description = serializers.SerializerMethodField()

    class Meta:
        model = ProductSubstitution
        fields = ('level', 'level_description', 'score')

    def get_level_description(self, obj):
        return obj.get_level_display()

    def to_representation(self, instance):
        representation = {
            'level': instance.level,
            'level_description': self.get_level_description(instance),
            'score': instance.score,
        }

        original_product_id = self.context.get('original_product_id')
        if instance.product_a.id == original_product_id:
            substitute_product = instance.product_b
        else:
            substitute_product = instance.product_a

        product_data = ProductSerializer(substitute_product, context=self.context).data
        representation.update(product_data)

        return representation
