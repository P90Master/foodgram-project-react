from django.contrib import admin
from django.contrib.admin.views.main import ChangeList

from .models import Tag, Ingredient, Recipe

EMPTY = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
        'color',
        'colored_name',
    )

    list_editable = (
        'name', 'slug', 'color',
    )

    search_fields = ('name',)
    empty_value_display = EMPTY


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )

    list_editable = (
        'name', 'measurement_unit'
    )

    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = EMPTY


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
    )

    list_editable = (
        'name', 'author', 'image', 'text', 'cooking_time'
    )

    search_fields = ('name',)
    empty_value_display = EMPTY
