from django.contrib import admin

from .models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientRecipeRelation
)

EMPTY = '-пусто-'


class TagInline(admin.StackedInline):
    model = Recipe.tags.through


class IngredientInline(admin.StackedInline):
    model = IngredientRecipeRelation
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
        'color',
        'colored_name',
    )

    inlines = (TagInline, )

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

    inlines = (IngredientInline,)

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
        'cooking_time'
    )

    inlines = (TagInline, IngredientInline)

    list_editable = (
        'name', 'author', 'image', 'text', 'cooking_time'
    )

    search_fields = ('name', 'author')
    empty_value_display = EMPTY


@admin.register(IngredientRecipeRelation)
class IngredientRecipeRelation(admin.ModelAdmin):
    list_display = (
        'pk',
        'recipe',
        'ingredient',
        'amount'
    )

    list_editable = (
        'recipe', 'ingredient', 'amount'
    )

    empty_value_display = EMPTY


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe',
    )

    list_editable = (
        'user', 'recipe'
    )

    empty_value_display = EMPTY


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe',
    )

    list_editable = (
        'user', 'recipe'
    )

    empty_value_display = EMPTY
