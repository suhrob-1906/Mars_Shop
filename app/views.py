from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Sum
from django.shortcuts import render, redirect, get_object_or_404

from .models import Product, CartItem, Category, Order, OrderItem, Review
from .api_views import get_session_key


User = get_user_model()


def welcome_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    return render(request, "welcome.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    errors = []
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        if not username:
            errors.append("Введите имя пользователя.")
        if not password1 or not password2:
            errors.append("Введите пароль и его подтверждение.")
        if password1 != password2:
            errors.append("Пароли не совпадают.")
        if len(password1) < 4:
            errors.append("Пароль должен быть не короче 4 символов.")
        if User.objects.filter(username=username).exists():
            errors.append("Пользователь с таким именем уже существует.")

        if not errors:
            user = User.objects.create_user(username=username, password=password1)
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect("index")

    return render(request, "register.html", {"errors": errors})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    errors = []
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)
        if user is None:
            errors.append("Неверное имя пользователя или пароль.")
        else:
            login(request, user)
            session_key = get_session_key(request)
            guest_items = CartItem.objects.filter(
                session_key=session_key,
                user__isnull=True,
            )
            for item in guest_items:
                existing = CartItem.objects.filter(
                    user=user,
                    product=item.product,
                ).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                    item.delete()
                else:
                    item.user = user
                    item.session_key = None
                    item.save()

            messages.success(request, "Вы успешно вошли!")
            return redirect("index")

    return render(request, "login.html", {"errors": errors})


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect("welcome")


def index_view(request):
    if not request.user.is_authenticated:
        return redirect("welcome")

    products = Product.objects.all().select_related("category")
    categories = Category.objects.all().order_by("name")

    search_query = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price") or ""
    max_price = request.GET.get("max_price") or ""
    sort = request.GET.get("sort") or "new"
    category_id = request.GET.get("category")

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    active_category = None
    if category_id:
        try:
            active_category = int(category_id)
            products = products.filter(category_id=active_category)
        except ValueError:
            active_category = None

    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    else:
        products = products.order_by("-created_at")

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "categories": categories,
        "page_obj": page_obj,
        "active_category": active_category,
        "search_query": search_query,
        "min_price": min_price,
        "max_price": max_price,
        "current_sort": sort,
        "title": "Каталог",
    }
    return render(request, "index.html", context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = Review.objects.filter(product=product).select_related("user")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]

    can_review = False
    if request.user.is_authenticated:
        has_order = OrderItem.objects.filter(
            order__user=request.user,
            order__status="completed",
            product=product,
        ).exists()
        already_reviewed = Review.objects.filter(
            user=request.user,
            product=product,
        ).exists()
        can_review = has_order and not already_reviewed

    context = {
        "product": product,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "can_review": can_review,
        "title": product.name,
    }
    return render(request, "product_detail.html", context)


def add_review_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if not request.user.is_authenticated:
        messages.error(request, "Сначала войдите в аккаунт.")
        return redirect("login")

    has_order = OrderItem.objects.filter(
        order__user=request.user,
        order__status="completed",
        product=product,
    ).exists()
    if not has_order:
        messages.error(request, "Вы можете оставить отзыв только после покупки товара.")
        return redirect("product_detail", pk=pk)

    if request.method == "POST":
        rating = int(request.POST.get("rating", 5))
        text = (request.POST.get("text") or "").strip()
        rating = max(1, min(5, rating))

        review, created = Review.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"rating": rating, "text": text},
        )
        if not created:
            review.rating = rating
            review.text = text
            review.save()

        messages.success(request, "Спасибо за отзыв!")
        return redirect("product_detail", pk=pk)

    return render(request, "add_review.html", {
        "product": product,
        "title": f"Отзыв — {product.name}",
    })


def cart_view(request):
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user).select_related("product")
    else:
        session_key = get_session_key(request)
        items = CartItem.objects.filter(
            session_key=session_key,
            user__isnull=True,
        ).select_related("product")

    cart_total = sum(i.total_price for i in items)

    return render(request, "cart.html", {
        "items": items,
        "cart_total": cart_total,
        "title": "Корзина",
    })


def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    can_review_any = False
    reviewable_products = []

    if request.user.is_authenticated and order.user == request.user:
        items = OrderItem.objects.filter(order=order).select_related("product")
        for item in items:
            has_review = Review.objects.filter(
                user=request.user,
                product=item.product,
            ).exists()
            if not has_review:
                can_review_any = True
                reviewable_products.append(item.product)

    context = {
        "order": order,
        "can_review_any": can_review_any,
        "reviewable_products": reviewable_products,
        "title": "Заказ оформлен",
    }
    return render(request, "order_success.html", context)


def order_reviews_view(request, order_id):

    if not request.user.is_authenticated:
        messages.error(request, "Сначала войдите в аккаунт.")
        return redirect("login")

    order = get_object_or_404(Order, id=order_id, user=request.user)

    items = (
        OrderItem.objects
        .filter(order=order)
        .select_related("product")
    )

    products_info = []
    for it in items:
        has_review = Review.objects.filter(
            user=request.user,
            product=it.product,
        ).exists()
        products_info.append({
            "product": it.product,
            "quantity": it.quantity,
            "has_review": has_review,
        })

    context = {
        "order": order,
        "products_info": products_info,
        "title": "Оставить отзывы",
    }
    return render(request, "order_reviews.html", context)


def admin_dashboard_view(request):
    total_orders = Order.objects.filter(status="completed").count()
    total_revenue = Order.objects.filter(status="completed").aggregate(
        s=Sum("total_price")
    )["s"] or 0
    total_users = User.objects.count()

    context = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_users": total_users,
        "title": "Админский дашборд",
    }
    return render(request, "admin_dashboard.html", context)
