from rest_framework.pagination import PageNumberPagination

from foodgram.settings import PAGINATION_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
