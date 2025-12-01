from rest_framework import serializers
from companies.models.postcode import Postcode

class PostcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Postcode
        fields = ('postcode', 'latitude', 'longitude', 'state')
