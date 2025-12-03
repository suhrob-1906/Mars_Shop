from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, Order, OrderItem, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "preview")
    list_filter = ("category",)
    search_fields = ("name", "category__name")

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "category", "description"),
        }),
        ("Цена", {
            "fields": ("price",),
        }),
        ("Изображение", {
            "fields": ("photo",),
        }),
    )

    def preview(self, obj):
        if obj.photo:
            return format_html(
                "<img src='{}' style='height:60px;border-radius:10px;object-fit:cover;'>",
                obj.photo.url,
            )
        return "—"

    preview.short_description = "Фото"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product", "quantity", "unit_price", "total_price")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username")
