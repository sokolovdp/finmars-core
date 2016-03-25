from rest_framework.pagination import PageNumberPagination


class HistoricalPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'size'
    page_size = 5
    max_page_size = 10
