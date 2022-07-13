import base64, uuid
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import APIException
from django.core.files.base import ContentFile

from recipes.models import Tag, Ingredient, Recipe, IngredientRecipeRelation

from .filters import queryset_cutter

User = get_user_model()

def relation_creator(instance, ingredients):
    relations = (
        IngredientRecipeRelation(
            recipe=instance,
            ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
        ) for ingredient in ingredients
    )

    IngredientRecipeRelation.objects.bulk_create(
            relations
    )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(imgstr), name = id.urn[9:] + '.' + ext
            )

        return super(Base64ImageField, self).to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    is_subscribed = serializers.SerializerMethodField()

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user
    
    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        
        try:
            return user.is_subscribed(author)
        except AttributeError:
            return 'Авторизируйтесь, чтобы подписаться'

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Имя me запрещено'
            )

        return username
    
    def validate(self, attrs):
        user = self.context.get('request').user
        assert user is not None

        try:
            validate_password(attrs['password'], user)

        except django_exceptions.ValidationError as error:
            raise serializers.ValidationError(
                {'password': list(error.messages)}
            )
        except KeyError:
            pass

        return super().validate(attrs)

    class Meta:
        fields = (
            'username', 'email', 'password', 'first_name',
            'last_name', 'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}
        model = User


class UserSetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    def validate(self, attrs):
        user = self.context.get('request').user
        assert user is not None

        is_password_valid = user.check_password(attrs['current_password'])
        if not is_password_valid:
            return self.fail('Неверный текущий пароль')

        try:
            validate_password(attrs['new_password'], user)

        except django_exceptions.ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )

        return super().validate(attrs)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'slug', 'color')
        model = Tag


class IngredientRecipeRelationSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipeRelation
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    ingredients = ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, recipe):
        relation = IngredientRecipeRelation.objects.filter(recipe=recipe)
        serializer = IngredientRecipeRelationSerializer(relation, many=True)
        return serializer.data

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user

        return recipe.is_favorited(user)
    
    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user

        return recipe.is_in_shopping_cart(user)

    class Meta:
        fields = '__all__'
        model = Recipe


class PostRecipeSerializer(RecipeSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    def get_ingredients(self, recipe):
        relation = IngredientRecipeRelation.objects.filter(recipe=recipe)
        serializer = IngredientRecipeRelationSerializer(relation, many=True)
        return serializer.data
    
    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        ingredients = request.data['ingredients']
        recipe.tags.set(tags)
        
        relation_creator(recipe, ingredients)

        recipe.save()

        return recipe
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )

        tags = validated_data.get('tags')
        if tags:
            instance.tags.set(tags)
        
        ingredients = request.data.get('ingredients')
        if ingredients:
            # Удаление старых связей
            old_ingredients_relations = instance.ingredients.all()
            for ingredient in old_ingredients_relations:
                instance.ingredients.remove(ingredient)

            # Создание новых        
            relation_creator(instance, ingredients)

        instance.save()

        return instance
    
    def validate_tags(self, tags):
        if tags is None or len(tags) == 0:
            raise serializers.ValidationError(
                'Отсутствуют теги'
            )

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Теги повторяются'
            )
        
        return tags
    
    def validate(self, attrs):
        '''
        Валидация поля ингредиентов.
        '''
        request = self.context.get('request')
        ingredients = request.data.get('ingredients')

        if not isinstance(ingredients, list) or len(ingredients) == 0:
            raise serializers.ValidationError(
                {'ingredients': 'Список ингредиентов пуст или некорректен'}
            )
        
        ingredients_ids = []

        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                raise serializers.ValidationError(
                    {'ingredients': 'Ожидается словарь-ингредиент'}
                )

            try:
                id = ingredient['id']
                if Ingredient.objects.filter(id=id).first() is None:
                    raise serializers.ValidationError(
                        {'ingredients': 'Несуществующий ингредиент(ы)'}
                    )

                amount = ingredient['amount']
                if not isinstance(amount, int) or amount < 1:
                    raise serializers.ValidationError(
                        {'ingredients': 'Неккоректное количество ингредиента'}
                    )
            
                ingredients_ids.append(id)
            except KeyError:
                raise serializers.ValidationError(
                        {'ingredients': 'Отсутствуют необходимые поля'}
                    )
            except ValueError:
                raise serializers.ValidationError(
                        {'ingredients': 'Неккоректные значения полей'}
                    )
        
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты повторяются'}
            )

        return attrs
    
    class Meta:
        model = Recipe
        fields = '__all__'


class SubscriptionSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    recipes = serializers.SerializerMethodField()
    
    def get_recipes(self, author):
        limit_value = self.context.get('request').GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=author)
        
        if limit_value:
            queryset = queryset_cutter(queryset, limit_value)

        return queryset.values('name', 'image', 'cooking_time')


    class Meta:
        fields = (
            'username', 'email', 'password', 'first_name',
            'last_name', 'is_subscribed', 'recipes', 'recipes_count'
        )
        extra_kwargs = {'password': {'write_only': True}}
        model = User
