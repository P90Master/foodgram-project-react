from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from django.db.utils import IntegrityError
from django.http.response import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from djoser.utils import logout_user

from rest_framework import viewsets, filters, status, mixins, generics
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)

from .permissions import (
    OnlyForAdmin,
    IsAuthorOrReadOnly,
    NoRoleChange,
)

from .serializers import (
    UserSerializer,
    UserSetPasswordSerializer,
    SubscriptionSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    PostRecipeSerializer
)

from .pagination import FoodgramPagination

from .filters import (
    FoodgramBaseFilter,
    RecipeFilter,
    IngredientFilter,
)

from users.models import Follow
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientRecipeRelation
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('date_joined')
    serializer_class = UserSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FoodgramBaseFilter
   
    def get_permissions(self):
        if self.action in ['create', 'list', 'get']:
            permission_classes = [AllowAny, ]
        elif self.action in ['patch', 'delete']:
            permission_classes = [OnlyForAdmin, ]
        else:
            permission_classes = [IsAuthenticated, ]

        return [permission() for permission in permission_classes]

    @action(
        methods=['post',],
        detail=False,
        url_path='set_password',
        serializer_class=UserSetPasswordSerializer,
        permission_classes=(IsAuthenticated, )
    )
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()

        logout_user(self.request)

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated, NoRoleChange)
    )
    def users_profile(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(role=user.role, password=user.password, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(
        methods=['post', 'delete'],
        detail=False,
        url_path=r'(?P<user_id>\d+)/subscribe',
        permission_classes=(IsAuthenticated, )
    )
    def subscribe(self, request, user_id):
        author = get_object_or_404(User, pk=user_id)
        user = request.user

        if request.method == 'DELETE':
            try:
                followship = Follow.objects.get(
                    user=user,
                    author=author
                )
                followship.delete()

            except Follow.DoesNotExist:
                error = {
                    'error': 'Вы не были подписаны на этого пользователя'
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            if user != author:
                Follow.objects.get_or_create(user=user, author=author)
        
            context = self.get_serializer(author).data
        
            return Response(context, status=status.HTTP_200_OK)
    
    @action(
        methods=['get',],
        detail=False,
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
        filter_backends=(DjangoFilterBackend,),
        filterset_class=FoodgramBaseFilter
    )
    def subscribtions(self, request):
        user = request.user
        wanted_ids = [following.author.id for following in user.followings.all()]
        subscriptions = User.objects.filter(id__in=wanted_ids).order_by('-id')
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(subscriptions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.get_queryset().order_by('id')
    serializer_class = RecipeSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'get']:
            permission_classes = [AllowAny, ]
        elif self.action == 'post':
            permission_classes = [IsAuthenticated, ]
        else:
            permission_classes = [IsAuthorOrReadOnly, ]

        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer

        return PostRecipeSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(
        methods=['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = request.user

        if request.method == 'DELETE':
            try:
                favoriteship = Favorite.objects.get(
                    user=user,
                    recipe=recipe
                )
                favoriteship.delete()

            except Favorite.DoesNotExist:
                error = {
                    'error': 'Вы не добавляли этот рецепт в избранное'
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            Favorite.objects.get_or_create(user=user, recipe=recipe)

            serializer = self.get_serializer(recipe)
            context = {
                'id': serializer.data.get('id'),
                'name': serializer.data.get('name'),
                'image': serializer.data.get('image'),
                'cooking_time': serializer.data.get('cooking_time'),
            }
        
            return Response(context, status=status.HTTP_200_OK)

    @action(
        methods=['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = request.user

        if request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(
                    user=user,
                    recipe=recipe
                )
                shopping_cart.delete()

            except Favorite.DoesNotExist:
                error = {
                    'error': 'Вы не добавляли этот рецепт в корзину'
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)

            serializer = self.get_serializer(recipe)
            context = {
                'id': serializer.data.get('id'),
                'name': serializer.data.get('name'),
                'image': serializer.data.get('image'),
                'cooking_time': serializer.data.get('cooking_time'),
            }
        
            return Response(context, status=status.HTTP_200_OK)
    
    @action(
        methods=['get',],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_objects = user.shopping_cart.all()
        shopping_cart = {}
        response_list = []

        # Сборка ингредиентов в словарь
        for obj in shopping_cart_objects:
            recipe = obj.recipe
            ingredients = IngredientRecipeRelation.objects.filter(
                recipe=recipe
            )

            for ingredient in ingredients:
                name = ingredient.ingredient.name
                amount = ingredient.amount
                measurement_unit = ingredient.ingredient.measurement_unit

                if name in shopping_cart.keys():
                    shopping_cart[name]['amount'] += amount

                else:
                    shopping_cart[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }
        
        # Формирование списка
        for name in shopping_cart.keys():
            subject = shopping_cart[name]
            response_list.append(
                f'{name}: {subject["amount"]} {subject["measurement_unit"]}\n'
        )
            
        response_obj = HttpResponse(
            response_list,
            'Content-Type: text/plain'
        )
        response_obj['Content-Disposition'] = (
            'attachment;' 'filename="shopping_cart.txt"'
        )
    
        return response_obj


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action in ['list', 'get']:
            permission_classes = [AllowAny, ]
        else:
            permission_classes = [OnlyForAdmin, ]

        return [permission() for permission in permission_classes]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

    def get_permissions(self):
        if self.action in ['list', 'get']:
            permission_classes = [AllowAny, ]
        else:
            permission_classes = [OnlyForAdmin, ]

        return [permission() for permission in permission_classes]
