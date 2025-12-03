from django.urls import path
from . import api_views

urlpatterns = [
    path("products/", api_views.ProductListAPIView.as_view(), name="api-products"),
    path("cart/", api_views.CartListAPIView.as_view(), name="api-cart-list"),
    path("cart/add/", api_views.CartAddAPIView.as_view(), name="api-cart-add"),
    path("cart/update_qty/", api_views.CartUpdateQtyAPIView.as_view(), name="api-cart-update"),
    path("cart/clear/", api_views.CartClearAPIView.as_view(), name="api-cart-clear"),
    path("orders/create/", api_views.OrderCreateAPIView.as_view(), name="api-order-create"),
    path("stats/sales/", api_views.SalesStatsAPIView.as_view(), name="api-stats-sales"),
    path("stats/categories/", api_views.CategoriesStatsAPIView.as_view(), name="api-stats-categories"),
]
