import os
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.dispatch import receiver


User = get_user_model()


def validate_color(color_code):
    if color_code[0] != '#':
        raise ValidationError(
                'Код должен начинаться с символа #'
        )

    if len(color_code) != 7:
        raise ValidationError(
                'Длина кода не равняется 7'
        )

    try:
        int(color_code[1:], 16)
    except:
        raise ValidationError(
            'Код не является hex-числом'
        )


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(
        max_length=7,
        default="#ffffff",
        validators=[validate_color],
    )

    def colored_name(self):
        return format_html(
            '<span style="color: {};">{}</span>',
            self.color, self.name
        )
    
    class Meta:
        ordering = ['id']


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=32)

    class Meta:
        ordering = ['id']


class Recipe(models.Model):
    name = models.CharField(max_length=200, unique=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes'
    )
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField(max_length=5000)
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipeRelation',
        related_name='recipes',
    )

    def is_favorited(self, user):
        return Favorite.objects.filter(user=user, recipe=self).exists()

    def is_in_shopping_cart(self, user):
        return ShoppingCart.objects.filter(user=user, recipe=self).exists()

    class Meta:
        ordering = ['id']


class IngredientRecipeRelation(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='IngredientRecipeRelation'
            ),
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранное'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='В избранном'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='favorite'
            ),
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_cart'
            )
        ]


@receiver(models.signals.post_delete, sender=Recipe)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=Recipe)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = Recipe.objects.get(pk=instance.pk).image
    except Recipe.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
