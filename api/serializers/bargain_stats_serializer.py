from rest_framework import serializers
from data_management.models import BargainStats

class BargainStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BargainStats
        fields = ('key', 'data', 'updated_at')
