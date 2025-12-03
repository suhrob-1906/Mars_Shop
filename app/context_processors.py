from .models import CartItem
from .api_views import get_session_key


def cart_info(request):
    """
    Добавляет cart_count во все шаблоны.
    """
    try:
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
        else:
            session_key = get_session_key(request)
            items = CartItem.objects.filter(
                session_key=session_key,
                user__isnull=True,
            )
        cart_count = sum(i.quantity for i in items)
    except Exception:
        cart_count = 0

    return {"cart_count": cart_count}
