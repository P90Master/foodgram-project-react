from django_filters import rest_framework
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Ingredient

User = get_user_model()


def queryset_cutter(queryset, value):
    try:
        value = int(value)
    except ValueError:
        return queryset

    return queryset[:value] if value > 0 else queryset


class RecipeFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    tags = rest_framework.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = rest_framework.BooleanFilter(
        method='is_favorited_filter'
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='is_in_shopping_cart_filter',
    )

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user

        if value and not user.is_anonymous:
            return queryset.filter(users__user=user)

        return queryset
    
    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user

        if value and not user.is_anonymous:
            return queryset.filter(in_shopping_cart__user=user)

        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
