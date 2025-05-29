from django.contrib import admin

from .models import Category, Product, ImageProduct, Order, Review, Region, District, Payment,User


class ImageProductStackedInline(admin.StackedInline):
    model = ImageProduct
    extra = 1
    max_num = 5
    min_num = 1


class ReviewStackedInline(admin.StackedInline):
    model = Review
    extra = 0
    max_num = 5
    min_num = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    inlines = ImageProductStackedInline,


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(District)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_number', 'amount', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('user__username', 'card_number')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


