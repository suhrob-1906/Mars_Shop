from datetime import timedelta

from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product, CartItem, Order, OrderItem
from .serializers import ProductSerializer, CartItemSerializer


def get_session_key(request):
    """
    Гарантированно получаем session_key для гостя.
    """
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


class ProductListAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        qs = Product.objects.all()
        serializer = ProductSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class CartListAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user).select_related("product")
        else:
            session_key = get_session_key(request)
            items = CartItem.objects.filter(
                session_key=session_key,
                user__isnull=True,
            ).select_related("product")

        serializer = CartItemSerializer(items, many=True)
        cart_total = sum([i.total_price for i in items]) if items else 0
        return Response({"items": serializer.data, "cart_total": float(cart_total)})


class CartAddAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        product_id = request.data.get("product_id")
        qty = int(request.data.get("qty", 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            obj, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                session_key=None,
                defaults={"quantity": qty},
            )
        else:
            session_key = get_session_key(request)
            obj, created = CartItem.objects.get_or_create(
                session_key=session_key,
                user=None,
                product=product,
                defaults={"quantity": qty},
            )

        if not created:
            obj.quantity += qty
            obj.save()

        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
        else:
            items = CartItem.objects.filter(
                session_key=get_session_key(request),
                user__isnull=True,
            )
        cart_total = sum([i.total_price for i in items])

        return Response({"success": True, "cart_total": float(cart_total)})


class CartUpdateQtyAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        item_id = request.data.get("item_id")
        action = request.data.get("action")
        item = get_object_or_404(CartItem, id=item_id)

        if action == "increase":
            item.quantity += 1
            item.save()
        elif action == "decrease":
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
                return Response({"success": True, "deleted": True})

        if item.user:
            items = CartItem.objects.filter(user=item.user)
        else:
            items = CartItem.objects.filter(
                session_key=item.session_key,
                user__isnull=True,
            )

        cart_total = sum([i.total_price for i in items])
        return Response({
            "success": True,
            "new_qty": getattr(item, "quantity", 0),
            "item_total": float(getattr(item, "total_price", 0)),
            "cart_total": float(cart_total),
        })


class CartClearAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if request.user.is_authenticated:
            CartItem.objects.filter(user=request.user).delete()
        else:
            session_key = get_session_key(request)
            CartItem.objects.filter(
                session_key=session_key,
                user__isnull=True,
            ).delete()
        return Response({"success": True})


class OrderCreateAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
            user = request.user
        else:
            session_key = get_session_key(request)
            items = CartItem.objects.filter(
                session_key=session_key,
                user__isnull=True,
            )
            user = None

        if not items.exists():
            return Response(
                {"success": False, "error": "cart empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.create(
            user=user,
            status="completed",
            created_at=timezone.now(),
        )

        total = 0
        for i in items:
            OrderItem.objects.create(
                order=order,
                product=i.product,
                quantity=i.quantity,
                unit_price=i.product.price,
            )
            total += i.total_price

        order.total_price = total
        order.save()
        items.delete()

        return Response({"success": True, "order_id": order.id})


class SalesStatsAPIView(APIView):
    """
    /api/stats/sales/?days=30 — для line-графика по дням.
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        qs = (
            Order.objects.filter(
                created_at__gte=since,
                status="completed",
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("total_price"))
            .order_by("day")
        )

        labels = [entry["day"].strftime("%Y-%m-%d") for entry in qs]
        values = [float(entry["total"] or 0) for entry in qs]

        return Response({"labels": labels, "values": values})


class CategoriesStatsAPIView(APIView):
    """
    /api/stats/categories/?days=30 — для pie-чарта по категориям.
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        qs = (
            OrderItem.objects.filter(
                order__created_at__gte=since,
                order__status="completed",
            )
            .values("product__category__name")
            .annotate(revenue=Sum(F("quantity") * F("unit_price")))
            .order_by("-revenue")
        )

        labels = [entry["product__category__name"] for entry in qs]
        values = [float(entry["revenue"] or 0) for entry in qs]

        return Response({"labels": labels, "values": values})
