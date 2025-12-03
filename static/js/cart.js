function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function showToast(text) {
    const toast = document.createElement('div');
    toast.className = "toast";
    toast.innerText = text;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('visible'));

    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function parseJsonResponse(response) {
    let json = null;
    try {
        json = await response.json();
    } catch (e) {
        return { error: 'Неверный ответ сервера' };
    }
    if (!response.ok) {
        return { error: json && json.error ? json.error : ('Ошибка: ' + response.status) };
    }
    return json;
}

// Добавить в корзину
async function addToCart(productId) {
    try {
        const res = await fetch('/api/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ product_id: productId, qty: 1 })
        });
        const data = await parseJsonResponse(res);
        if (data.error) {
            showToast("Ошибка: " + data.error);
            return;
        }
        showToast("Товар добавлен в корзину");
    } catch (e) {
        console.error(e);
        showToast("Ошибка сети");
    }
}

// Изменить количество
async function changeQty(itemId, action) {
    try {
        const res = await fetch('/api/cart/update_qty/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ item_id: itemId, action: action })
        });
        const data = await parseJsonResponse(res);
        if (data.error) {
            showToast("Ошибка: " + data.error);
            return;
        }
        window.location.href = "/cart/";
    } catch (e) {
        console.error(e);
        showToast("Ошибка сети");
    }
}

// Очистить корзину
async function clearCart() {
    try {
        const res = await fetch('/api/cart/clear/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({})
        });
        const data = await parseJsonResponse(res);
        if (data.error) {
            showToast("Ошибка: " + data.error);
            return;
        }
        showToast("Корзина очищена");
        window.location.href = "/cart/";
    } catch (e) {
        console.error(e);
        showToast("Ошибка сети");
    }
}

// Оформить заказ
async function checkout() {
    try {
        const res = await fetch('/api/orders/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({})
        });
        const data = await parseJsonResponse(res);
        if (data.error) {
            showToast("Ошибка: " + data.error);
            return;
        }

        // красивое уведомление
        const overlay = document.createElement('div');
        overlay.className = 'order-overlay';
        overlay.innerHTML = `
            <div class="order-overlay-inner">
                <div style="font-size:42px;margin-bottom:10px;">✅</div>
                <h2 style="font-size:1.4rem;font-weight:800;margin-bottom:6px;">Заказ оформлен!</h2>
                <p style="font-size:0.95rem;opacity:0.9;">
                    Спасибо за покупку в Mars Shop.
                </p>
            </div>
        `;
        document.body.appendChild(overlay);

        const orderId = data.order_id;
        const targetUrl = orderId ? `/order/success/${orderId}/` : "/";

        setTimeout(() => {
            window.location.href = targetUrl;
        }, 1200);
    } catch (e) {
        console.error(e);
        showToast("Ошибка сети");
    }
}
