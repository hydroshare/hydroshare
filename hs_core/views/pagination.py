from rest_framework.pagination import PageNumberPagination


class SmallDatumPagination(PageNumberPagination):
    """ Only use for requests whose resulting datum elements are small and where
        one wants to force all results to be on one page
    """
    page_size = None
