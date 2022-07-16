from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from django.db.utils import IntegrityError
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
    RecipeFilter,
    IngredientFilter,
)
from .utils import shopping_cart_downloader
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

def objects_relations_manager(this, model, request, error, **kwargs):
    if request.method == 'DELETE':
        try:
            relation = model.objects.get(
                **kwargs
            )
            relation.delete()

        except model.DoesNotExist:
            error = {
                'error': error
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(status=status.HTTP_204_NO_CONTENT)

    model.objects.get_or_create(**kwargs)
    obj = list(kwargs.values())[1]
        
    context = this.get_serializer(obj).data
        
    return Response(context, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('date_joined')
    serializer_class = UserSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
   
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
        error_msg = 'Вы не были подписаны на этого пользователя'

        if user == author:
            error = {
                'error': 'Вы не можете подписаться сами на себя'
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        return objects_relations_manager(
            self, Follow, request, error_msg, user=user, author=author
        )
    
    @action(
        methods=['get',],
        detail=False,
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer,
        filter_backends=(DjangoFilterBackend,)
    )
    def subscribtions(self, request):
        user = request.user
        followings = user.followings.all()
        subscriptions = User.objects.filter(followers__in=followings).order_by('-id')
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(subscriptions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.get_queryset().order_by('-id')
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
        error_msg = 'Вы не добавляли этот рецепт в избранное'

        return objects_relations_manager(
            self, Favorite, request, error_msg, user=user, recipe=recipe
        )

    @action(
        methods=['post', 'delete'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = request.user
        error_msg = 'Вы не добавляли этот рецепт в корзину'

        return objects_relations_manager(
            self, ShoppingCart, request, error_msg, user=user, recipe=recipe
        )
    
    @action(
        methods=['get',],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_objects = user.shopping_cart.all()
        
        return shopping_cart_downloader(shopping_cart_objects)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ['list', 'get']:
            permission_classes = [AllowAny, ]
        else:
            permission_classes = [OnlyForAdmin, ]

        return [permission() for permission in permission_classes]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter

    def get_permissions(self):
        if self.action in ['list', 'get']:
            permission_classes = [AllowAny, ]
        else:
            permission_classes = [OnlyForAdmin, ]

        return [permission() for permission in permission_classes]
