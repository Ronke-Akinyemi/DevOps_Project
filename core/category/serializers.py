from rest_framework import serializers
from category.models import Category, CATEGORY_TYPE

class CategorySerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=[c[0] for c in CATEGORY_TYPE], required=False)
    class Meta:
        model = Category
        fields = ["id", "name", "type"]