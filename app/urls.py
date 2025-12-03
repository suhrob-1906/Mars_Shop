from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("welcome/", views.welcome_view, name="welcome"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("cart/", views.cart_view, name="cart"),

    path("product/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("product/<int:pk>/review/", views.add_review_view, name="add_review"),

    path("order/success/<int:order_id>/", views.order_success_view, name="order_success"),
    path("order/<int:order_id>/reviews/", views.order_reviews_view, name="order_reviews"),

    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
]
