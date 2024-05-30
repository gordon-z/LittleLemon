from rest_framework import serializers
from .models import MenuItem, Category
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']

    def create(self, validated_data):
        category_data = validated_data.pop('category')
        category = Category.objects.create(**category_data)
        menu_item = MenuItem.objects.create(category=category, **validated_data)
        return menu_item
    
    def update(self, instance, validated_data):
        category_data = validated_data.pop('category', None)
        if category_data:
            category_serializer = CategorySerializer(instance.category, data=category_data)
            category_serializer.is_valid(raise_exception=True)
            category_serializer.save()
        return super().update(instance, validated_data)
    
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
