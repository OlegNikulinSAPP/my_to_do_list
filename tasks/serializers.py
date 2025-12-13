from rest_framework import serializers
from .models import Task, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TaskSerializer(serializers.ModelSerializer):
    # Детали категорий для чтения
    categories = CategorySerializer(many=True, read_only=True)

    # Поле для приёма ID категорий при создании/обновлении
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source='categories',
        write_only=True,
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'deadline',
            'completed', 'created_at', 'author',
            'categories', 'category_ids'
        ]
        read_only_fields = ['author', 'created_at']