from rest_framework import serializers
from data_management.models import FAQ

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer')
