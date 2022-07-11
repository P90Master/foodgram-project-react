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


class FoodgramBaseFilter(rest_framework.FilterSet):
    limit = rest_framework.NumberFilter(
        method='limit_filter'
    )

    def limit_filter(self, queryset, name, value):
        return queryset_cutter(queryset, value)


class RecipeFilter(FoodgramBaseFilter):
    author = rest_framework.NumberFilter(
        field_name='author__id', lookup_expr='exact')
    tags = rest_framework.CharFilter(
        field_name='tags__slug', lookup_expr='exact')
    is_favorited = rest_framework.BooleanFilter(
        method='is_favorited_filter'
    )

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user

        wanted_ids = [
            rec.id for rec in queryset if rec.is_favorited(user) == value
        ]

        return queryset.filter(id__in=wanted_ids)

    class Meta:
        model = Recipe
        fields = ('author', 'tags')


class IngredientFilter(FoodgramBaseFilter):
    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
